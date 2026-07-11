from typing import Any, TypeVar

from sqlalchemy import Select, delete, func, or_, select, update

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.base_model import BaseModel
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.job import Job
from apps.base.models.notice import Notice
from apps.base.models.source import Source
from apps.base.models.user import UserRestriction

T = TypeVar("T", bound=BaseModel)


async def _paginate(stmt: Select[tuple[T]], current: int, size: int) -> tuple[list[T], int]:
    """
    执行运营管理分页查询。

    :param stmt: 查询语句。
    :param current: 当前页码。
    :param size: 每页条数。
    :return: 数据列表和总数。
    """
    offset, limit = db.page(current, size)
    total = await db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    records = await db.model_all(stmt.order_by(stmt.selected_columns.id.desc()).offset(offset).limit(limit))
    return list(records), int(total or 0)


async def _create(model: type[T], data: dict[str, Any]) -> T:
    """
    创建运营管理模型。

    :param model: 模型类。
    :param data: 创建数据。
    :return: 创建后的模型对象。
    """
    item = model(**data)
    async with db.atomic() as session:
        session.add(item)
        await session.flush()
        await session.refresh(item)
    return item


async def _update(item: T, data: dict[str, Any]) -> T:
    """
    更新运营管理模型。

    :param item: 模型对象。
    :param data: 更新数据。
    :return: 更新后的模型对象。
    """
    if not data:
        return item
    for key, value in data.items():
        setattr(item, key, value)
    await db.execute(update(type(item)).where(type(item).id == item.id).values(**data))
    return item


async def _delete(model: type[T], item_id: int) -> None:
    """
    根据主键删除运营管理模型。

    :param model: 模型类。
    :param item_id: 主键 ID。
    :return: None。
    """
    await db.execute(delete(model).where(model.id == item_id))


@Component()
class AdminOperationDao:
    """
    后台运营管理数据访问对象。
    """

    async def list_jobs(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        group: str | None = None,
        status: int | None = None,
    ) -> tuple[list[Job], int]:
        """
        分页查询定时任务。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 任务关键词。
        :param group: 任务组名。
        :param status: 任务状态。
        :return: 任务列表和总数。
        """
        stmt = select(Job)
        if keyword:
            stmt = stmt.where(or_(Job.name.ilike(f"%{keyword}%"), Job.invoke_target.ilike(f"%{keyword}%")))
        if group:
            stmt = stmt.where(Job.group == group)
        if status is not None:
            stmt = stmt.where(Job.status == status)
        return await _paginate(stmt, current, size)

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

    async def list_sources(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        user_id: int | None = None,
        is_deleted: bool | None = None,
    ) -> tuple[list[Source], int]:
        """
        分页查询资源。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 资源 URL 关键词。
        :param user_id: 用户 ID。
        :param is_deleted: 是否已删除。
        :return: 资源列表和总数。
        """
        stmt = select(Source)
        if keyword:
            stmt = stmt.where(Source.url.ilike(f"%{keyword}%"))
        if user_id:
            stmt = stmt.where(Source.user_id == user_id)
        if is_deleted is not None:
            stmt = stmt.where(Source.is_deleted == is_deleted)
        return await _paginate(stmt, current, size)

    async def get_source_by_id(self, source_id: int) -> Source | None:
        """
        根据 ID 查询资源。

        :param source_id: 资源 ID。
        :return: 资源对象。
        """
        return await db.model_first(select(Source).where(Source.id == source_id))

    async def update_source(self, source: Source, data: dict[str, Any]) -> Source:
        """
        更新资源。

        :param source: 资源对象。
        :param data: 更新数据。
        :return: 资源对象。
        """
        return await _update(source, data)

    async def delete_source(self, source_id: int) -> None:
        """
        删除资源。

        :param source_id: 资源 ID。
        :return: None。
        """
        await _delete(Source, source_id)

    async def list_notices(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        user_id: int | None = None,
        notice_type: int | None = None,
        is_read: bool | None = None,
    ) -> tuple[list[Notice], int]:
        """
        分页查询通知。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 通知关键词。
        :param user_id: 用户 ID。
        :param notice_type: 通知类型。
        :param is_read: 是否已读。
        :return: 通知列表和总数。
        """
        stmt = select(Notice)
        if keyword:
            stmt = stmt.where(or_(Notice.title.ilike(f"%{keyword}%"), Notice.content.ilike(f"%{keyword}%")))
        if user_id:
            stmt = stmt.where(Notice.user_id == user_id)
        if notice_type is not None:
            stmt = stmt.where(Notice.notice_type == notice_type)
        if is_read is not None:
            stmt = stmt.where(Notice.is_read == is_read)
        return await _paginate(stmt, current, size)

    async def get_notice_by_id(self, notice_id: int) -> Notice | None:
        """
        根据 ID 查询通知。

        :param notice_id: 通知 ID。
        :return: 通知对象。
        """
        return await db.model_first(select(Notice).where(Notice.id == notice_id))

    async def update_notice(self, notice: Notice, data: dict[str, Any]) -> Notice:
        """
        更新通知。

        :param notice: 通知对象。
        :param data: 更新数据。
        :return: 通知对象。
        """
        return await _update(notice, data)

    async def delete_notice(self, notice_id: int) -> None:
        """
        删除通知。

        :param notice_id: 通知 ID。
        :return: None。
        """
        await _delete(Notice, notice_id)

    async def list_user_restrictions(
        self,
        current: int,
        size: int,
        user_id: int | None = None,
        restrict_type: int | None = None,
        is_cancel: bool | None = None,
    ) -> tuple[list[UserRestriction], int]:
        """
        分页查询用户限制。

        :param current: 当前页码。
        :param size: 每页条数。
        :param user_id: 用户 ID。
        :param restrict_type: 限制类型。
        :param is_cancel: 是否解除。
        :return: 用户限制列表和总数。
        """
        stmt = select(UserRestriction)
        if user_id:
            stmt = stmt.where(UserRestriction.user_id == user_id)
        if restrict_type is not None:
            stmt = stmt.where(UserRestriction.restrict_type == restrict_type)
        if is_cancel is not None:
            stmt = stmt.where(UserRestriction.is_cancel == is_cancel)
        return await _paginate(stmt, current, size)

    async def get_user_restriction_by_id(self, restriction_id: int) -> UserRestriction | None:
        """
        根据 ID 查询用户限制。

        :param restriction_id: 用户限制 ID。
        :return: 用户限制对象。
        """
        return await db.model_first(select(UserRestriction).where(UserRestriction.id == restriction_id))

    async def create_user_restriction(self, data: dict[str, Any]) -> UserRestriction:
        """
        创建用户限制。

        :param data: 用户限制数据。
        :return: 用户限制对象。
        """
        return await _create(UserRestriction, data)

    async def update_user_restriction(self, restriction: UserRestriction, data: dict[str, Any]) -> UserRestriction:
        """
        更新用户限制。

        :param restriction: 用户限制对象。
        :param data: 更新数据。
        :return: 用户限制对象。
        """
        return await _update(restriction, data)

    async def delete_user_restriction(self, restriction_id: int) -> None:
        """
        删除用户限制。

        :param restriction_id: 用户限制 ID。
        :return: None。
        """
        await _delete(UserRestriction, restriction_id)
