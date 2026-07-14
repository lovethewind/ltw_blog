from typing import Any

from sqlalchemy import select

from apps.admin.dao.base_dao import _delete, _paginate, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.source import Source


@Component()
class AdminSourceDao:
    """后台资源数据访问对象。"""

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
        return await _paginate(stmt, current, size, Source.id.desc())

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
