import asyncio
import hashlib
import json
from contextlib import suppress
from typing import Any

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED, JobExecutionEvent
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from apps.base.constant.redis_constant import RedisConstant
from apps.base.core.depend_inject import GetBean, GetValue, logger
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.job import JobStatusEnum, MisfirePolicyEnum
from apps.base.models.job import Job
from apps.base.utils.redis_util import RedisUtil
from apps.scheduler.core.invoke import invoke_target, resolve_invoke_target

RECONCILE_JOB_ID = "system-job-reconciler"


def build_job_options(job: Job) -> dict[str, Any]:
    """将数据库任务策略转换为 APScheduler 参数。

    :param job: 数据库任务
    :return: APScheduler 执行参数
    """
    if job.misfire_policy == MisfirePolicyEnum.IMMEDIATELY.value:
        coalesce = False
        misfire_grace_time = None
    elif job.misfire_policy == MisfirePolicyEnum.EXECUTE_ONCE.value:
        coalesce = True
        misfire_grace_time = None
    else:
        coalesce = True
        misfire_grace_time = 1
    return {
        "coalesce": coalesce,
        "misfire_grace_time": misfire_grace_time,
        "max_instances": 10 if job.concurrent else 1,
    }


class DatabaseScheduler:
    """数据库任务与 APScheduler 对账服务。"""

    def __init__(self, scheduler: AsyncIOScheduler | None = None, redis_util: RedisUtil | None = None) -> None:
        """初始化数据库任务调度器。

        :param scheduler: 可选的 APScheduler 实例
        :param redis_util: 可选的 Redis 工具
        :return: None
        """
        timezone = GetValue("app.scheduler.timezone") or "Asia/Shanghai"
        self.scheduler = scheduler or AsyncIOScheduler(timezone=timezone)
        self.timezone = timezone
        self.redis_util = redis_util
        self._fingerprints: dict[str, str] = {}
        self._subscriber_task: asyncio.Task[None] | None = None
        self._pubsub: Any = None
        self._stopping = False

    async def start(self, interval_seconds: int = 300) -> None:
        """启动调度器并注册数据库对账任务。

        :param interval_seconds: 数据库任务对账间隔秒数
        :return: None
        """
        self.scheduler.add_listener(self._handle_job_event, EVENT_JOB_ERROR | EVENT_JOB_MISSED)
        self.scheduler.start()
        self.redis_util = self.redis_util or GetBean(RedisUtil)
        await self._open_subscription()
        self._subscriber_task = asyncio.create_task(self._listen_job_changes(), name="scheduler-job-change-subscriber")
        await self.reconcile_jobs()
        self.scheduler.add_job(
            self.reconcile_jobs,
            trigger="interval",
            seconds=interval_seconds,
            id=RECONCILE_JOB_ID,
            name="数据库定时任务对账",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        logger.info(f"定时任务服务已启动，对账间隔 {interval_seconds} 秒")

    async def shutdown(self) -> None:
        """关闭 Redis 订阅和 APScheduler。

        :return: None
        """
        self._stopping = True
        if self._subscriber_task:
            self._subscriber_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._subscriber_task
            self._subscriber_task = None
        await self._close_subscription()
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)

    async def reconcile_jobs(self) -> None:
        """将数据库启用任务同步到 APScheduler。

        :return: None
        """
        jobs = await self._load_enabled_jobs()
        active_ids: set[str] = set()
        for job in jobs:
            scheduler_job_id = self._scheduler_job_id(job.id)
            active_ids.add(scheduler_job_id)
            self._upsert_job(job)
        stale_ids = set(self._fingerprints) - active_ids
        for scheduler_job_id in stale_ids:
            self.scheduler.remove_job(scheduler_job_id)
            self._fingerprints.pop(scheduler_job_id, None)

    async def reconcile_job(self, job_id: int) -> None:
        """对账单个数据库定时任务。

        :param job_id: 数据库任务 ID
        :return: None
        """
        scheduler_job_id = self._scheduler_job_id(job_id)
        job = await self._load_job(job_id)
        if job:
            self._upsert_job(job)
            return
        if scheduler_job_id in self._fingerprints:
            self.scheduler.remove_job(scheduler_job_id)
            self._fingerprints.pop(scheduler_job_id, None)

    async def handle_change_message(self, data: str | bytes) -> None:
        """解析 Redis 任务变更消息并触发单任务对账。

        :param data: Redis 消息内容
        :return: None
        """
        try:
            payload = json.loads(data)
            job_id = payload.get("job_id")
            if not isinstance(job_id, int) or job_id <= 0:
                raise ValueError("job_id 无效")
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning(f"忽略无效的定时任务变更消息：{data!r}，原因：{exc}")
            return
        await self.reconcile_job(job_id)

    async def execute_job(self, target: str) -> Any:
        """执行单个数据库定时任务。

        :param target: 点分隔的调用目标
        :return: 调用结果
        """
        logger.info(f"开始执行定时任务：{target}")
        result = await invoke_target(target)
        logger.info(f"定时任务执行完成：{target}")
        return result

    async def _load_enabled_jobs(self) -> list[Job]:
        """读取数据库中启用的定时任务。

        :return: 启用任务列表
        """
        jobs = await db.model_all(select(Job).where(Job.status == JobStatusEnum.NORMAL.value))
        return list(jobs)

    async def _load_job(self, job_id: int) -> Job | None:
        """读取单个启用的数据库定时任务。

        :param job_id: 数据库任务 ID
        :return: 启用的任务；任务不存在或暂停时返回 None
        """
        return await db.model_first(select(Job).where(Job.id == job_id, Job.status == JobStatusEnum.NORMAL.value))

    def _upsert_job(self, job: Job) -> None:
        """向 APScheduler 新增或更新数据库任务。

        :param job: 数据库任务
        :return: None
        """
        scheduler_job_id = self._scheduler_job_id(job.id)
        fingerprint = self._fingerprint(job)
        if self._fingerprints.get(scheduler_job_id) == fingerprint:
            return
        try:
            resolve_invoke_target(job.invoke_target)
            trigger = CronTrigger.from_crontab(job.cron_expression, timezone=self.timezone)
            options = build_job_options(job)
            self.scheduler.add_job(
                self.execute_job,
                trigger=trigger,
                id=scheduler_job_id,
                name=job.name,
                args=[job.invoke_target],
                replace_existing=True,
                **options,
            )
            self._fingerprints[scheduler_job_id] = fingerprint
        except (ImportError, TypeError, ValueError) as exc:
            logger.error(f"加载定时任务[{job.id}:{job.name}]失败：{exc}")
            self._fingerprints.pop(scheduler_job_id, None)

    async def _open_subscription(self) -> None:
        """打开 Redis 定时任务变更订阅。

        :return: None
        """
        if not self.redis_util:
            raise RuntimeError("Redis 工具尚未初始化")
        self._pubsub = self.redis_util.redis.pubsub(ignore_subscribe_messages=True)
        await self._pubsub.subscribe(RedisConstant.SCHEDULER_JOB_CHANGED_CHANNEL)

    async def _close_subscription(self) -> None:
        """关闭 Redis 定时任务变更订阅。

        :return: None
        """
        if not self._pubsub:
            return
        with suppress(Exception):
            await self._pubsub.unsubscribe(RedisConstant.SCHEDULER_JOB_CHANGED_CHANNEL)
            await self._pubsub.aclose()
        self._pubsub = None

    async def _listen_job_changes(self) -> None:
        """持续监听 Redis 定时任务变更消息并自动重连。

        :return: None
        """
        while not self._stopping:
            try:
                async for message in self._pubsub.listen():
                    await self.handle_change_message(message["data"])
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error(f"定时任务变更订阅异常，1 秒后重连：{exc}")
                await self._close_subscription()
                await asyncio.sleep(1)
                if not self._stopping:
                    await self._open_subscription()

    def _fingerprint(self, job: Job) -> str:
        """计算影响调度行为的任务配置指纹。

        :param job: 数据库任务
        :return: 配置指纹
        """
        raw = "|".join(
            str(value)
            for value in (
                job.name,
                job.invoke_target,
                job.cron_expression,
                job.misfire_policy,
                job.concurrent,
            )
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _scheduler_job_id(self, job_id: int) -> str:
        """生成数据库任务对应的调度器任务 ID。

        :param job_id: 数据库任务 ID
        :return: 调度器任务 ID
        """
        return f"db-job-{job_id}"

    def _handle_job_event(self, event: JobExecutionEvent) -> None:
        """记录任务错过或执行失败事件。

        :param event: APScheduler 任务事件
        :return: None
        """
        if event.code == EVENT_JOB_MISSED:
            logger.warning(f"定时任务[{event.job_id}]错过执行时间")
            return
        if event.exception:
            logger.error(f"定时任务[{event.job_id}]执行失败：{event.exception}")
