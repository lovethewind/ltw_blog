from typing import Any

from sqlalchemy import or_, select

from apps.admin.dao.base_dao import _create, _delete, _paginate, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.job import Job


@Component()
class AdminJobDao:
    """后台定时任务数据访问对象。"""

    async def list_jobs(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        group: str | None = None,
        status: int | None = None,
        create_user_id: int | None = None,
    ) -> tuple[list[Job], int]:
        """
        分页查询定时任务。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 任务关键词。
        :param group: 任务组名。
        :param status: 任务状态。
        :param create_user_id: 创建者 ID。
        :return: 任务列表和总数。
        """
        stmt = select(Job)
        if keyword:
            stmt = stmt.where(or_(Job.name.ilike(f"%{keyword}%"), Job.invoke_target.ilike(f"%{keyword}%")))
        if group:
            stmt = stmt.where(Job.group == group)
        if status is not None:
            stmt = stmt.where(Job.status == status)
        if create_user_id:
            stmt = stmt.where(Job.create_user_id == create_user_id)
        return await _paginate(stmt, current, size, Job.id.desc())

    async def get_job_by_id(self, job_id: int) -> Job | None:
        """
        根据 ID 查询定时任务。

        :param job_id: 任务 ID。
        :return: 任务对象。
        """
        return await db.model_first(select(Job).where(Job.id == job_id))

    async def create_job(self, data: dict[str, Any]) -> Job:
        """
        创建定时任务。

        :param data: 任务数据。
        :return: 任务对象。
        """
        return await _create(Job, data)

    async def update_job(self, job: Job, data: dict[str, Any]) -> Job:
        """
        更新定时任务。

        :param job: 任务对象。
        :param data: 更新数据。
        :return: 任务对象。
        """
        return await _update(job, data)

    async def delete_job(self, job_id: int) -> None:
        """
        删除定时任务。

        :param job_id: 任务 ID。
        :return: None。
        """
        await _delete(Job, job_id)
