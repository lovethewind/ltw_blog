import json

from redis.exceptions import RedisError

from apps.admin.dao.job_dao import AdminJobDao
from apps.admin.dto.job_dto import AdminJobDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.job_vo import AdminJobCreateVO, AdminJobQueryVO, AdminJobStatusVO, AdminJobUpdateVO
from apps.base.constant.redis_constant import RedisConstant
from apps.base.core.depend_inject import Autowired, Component, logger
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.utils.redis_util import RedisUtil


@Component()
class AdminJobService(AdminBaseService):
    """后台定时任务服务。"""

    admin_job_dao: AdminJobDao = Autowired()
    redis_util: RedisUtil = Autowired()

    async def list_jobs(self, query_vo: AdminJobQueryVO) -> dict:
        """
        分页查询定时任务。

        :param query_vo: 定时任务查询参数
        :return: 定时任务分页数据
        """
        jobs, total = await self.admin_job_dao.list_jobs(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.group,
            query_vo.status,
            query_vo.create_user_id,
        )
        records = AdminJobDTO.bulk_model_validate(jobs)
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_job(self, job_id: int) -> AdminJobDTO:
        """
        查询定时任务详情。

        :param job_id: 定时任务 ID
        :return: 定时任务详情
        :raises MyException: 定时任务不存在时抛出
        """
        job = await self.admin_job_dao.get_job_by_id(job_id)
        if not job:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminJobDTO.model_validate(job)

    async def create_job(self, job_vo: AdminJobCreateVO) -> AdminJobDTO:
        """
        创建定时任务。

        :param job_vo: 定时任务创建参数
        :return: 定时任务详情
        """
        data = job_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        job = await self.admin_job_dao.create_job(data)
        await self._publish_job_change(job.id)
        return AdminJobDTO.model_validate(job)

    async def update_job(self, job_id: int, job_vo: AdminJobUpdateVO) -> AdminJobDTO:
        """
        更新定时任务。

        :param job_id: 定时任务 ID
        :param job_vo: 定时任务更新参数
        :return: 定时任务详情
        :raises MyException: 定时任务不存在时抛出
        """
        job = await self.admin_job_dao.get_job_by_id(job_id)
        if not job:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = job_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        job = await self.admin_job_dao.update_job(job, data)
        await self._publish_job_change(job.id)
        return AdminJobDTO.model_validate(job)

    async def update_job_status(self, job_id: int, status_vo: AdminJobStatusVO) -> AdminJobDTO:
        """
        更新定时任务状态。

        :param job_id: 定时任务 ID
        :param status_vo: 状态更新参数
        :return: 定时任务详情
        :raises MyException: 定时任务不存在时抛出
        """
        job = await self.admin_job_dao.get_job_by_id(job_id)
        if not job:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = status_vo.model_dump(exclude_none=True)
        job = await self.admin_job_dao.update_job(job, data)
        await self._publish_job_change(job.id)
        return AdminJobDTO.model_validate(job)

    async def delete_job(self, job_id: int) -> None:
        """
        删除定时任务。

        :param job_id: 定时任务 ID
        :return: None
        :raises MyException: 定时任务不存在时抛出
        """
        job = await self.admin_job_dao.get_job_by_id(job_id)
        if not job:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_job_dao.delete_job(job_id)
        await self._publish_job_change(job_id)

    async def _publish_job_change(self, job_id: int) -> None:
        """发布定时任务配置变更事件。

        :param job_id: 定时任务 ID
        :return: None
        """
        payload = json.dumps({"job_id": job_id})
        try:
            await self.redis_util.redis.publish(RedisConstant.SCHEDULER_JOB_CHANGED_CHANNEL, payload)
        except RedisError as exc:
            logger.warning(f"发布定时任务[{job_id}]变更事件失败，将由定期对账补偿：{exc}")
