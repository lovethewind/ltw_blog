from typing import Any

from sqlalchemy import or_, select

from apps.admin.dao.base_dao import _create, _delete, _paginate, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.link import Link


@Component()
class AdminLinkDao:
    """后台友链数据访问对象。"""

    async def list_links(
        self, current: int, size: int, keyword: str | None = None, status: int | None = None
    ) -> tuple[list[Link], int]:
        """
        分页查询友链。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 友链关键词。
        :param status: 审核状态。
        :return: 友链列表和总数。
        """
        stmt = select(Link)
        if keyword:
            stmt = stmt.where(
                or_(Link.name.ilike(f"%{keyword}%"), Link.url.ilike(f"%{keyword}%"), Link.email.ilike(f"%{keyword}%"))
            )
        if status is not None:
            stmt = stmt.where(Link.status == status)
        return await _paginate(stmt, current, size, Link.index, Link.id.desc())

    async def get_link_by_id(self, link_id: int) -> Link | None:
        """
        根据 ID 查询友链。

        :param link_id: 友链 ID。
        :return: 友链对象。
        """
        return await db.model_first(select(Link).where(Link.id == link_id))

    async def create_link(self, data: dict[str, Any]) -> Link:
        """
        创建友链。

        :param data: 友链数据。
        :return: 友链对象。
        """
        return await _create(Link, data)

    async def update_link(self, link: Link, data: dict[str, Any]) -> Link:
        """
        更新友链。

        :param link: 友链对象。
        :param data: 更新数据。
        :return: 友链对象。
        """
        return await _update(link, data)

    async def delete_link(self, link_id: int) -> None:
        """
        删除友链。

        :param link_id: 友链 ID。
        :return: None。
        """
        await _delete(Link, link_id)
