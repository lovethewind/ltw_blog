from typing import Any

from sqlalchemy import or_, select

from apps.admin.dao.base_dao import _create, _delete, _paginate, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.website import Website


@Component()
class AdminWebsiteDao:
    """后台网站导航数据访问对象。"""

    async def list_websites(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        category_id: int | None = None,
        status: int | None = None,
        user_id: int | None = None,
    ) -> tuple[list[Website], int]:
        """
        分页查询网站导航。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 网站关键词。
        :param category_id: 分类 ID。
        :param status: 审核状态。
        :param user_id: 用户 ID。
        :return: 网站导航列表和总数。
        """
        stmt = select(Website)
        if keyword:
            stmt = stmt.where(
                or_(
                    Website.name.ilike(f"%{keyword}%"),
                    Website.url.ilike(f"%{keyword}%"),
                    Website.introduce.ilike(f"%{keyword}%"),
                )
            )
        if category_id:
            stmt = stmt.where(Website.category_id == category_id)
        if status is not None:
            stmt = stmt.where(Website.status == status)
        if user_id:
            stmt = stmt.where(Website.user_id == user_id)
        return await _paginate(stmt, current, size, Website.index, Website.id.desc())

    async def get_website_by_id(self, website_id: int) -> Website | None:
        """
        根据 ID 查询网站导航。

        :param website_id: 网站导航 ID。
        :return: 网站导航对象。
        """
        return await db.model_first(select(Website).where(Website.id == website_id))

    async def create_website(self, data: dict[str, Any]) -> Website:
        """
        创建网站导航。

        :param data: 网站导航数据。
        :return: 网站导航对象。
        """
        return await _create(Website, data)

    async def update_website(self, website: Website, data: dict[str, Any]) -> Website:
        """
        更新网站导航。

        :param website: 网站导航对象。
        :param data: 更新数据。
        :return: 网站导航对象。
        """
        return await _update(website, data)

    async def delete_website(self, website_id: int) -> None:
        """
        删除网站导航。

        :param website_id: 网站导航 ID。
        :return: None。
        """
        await _delete(Website, website_id)
