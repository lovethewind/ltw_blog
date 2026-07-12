from typing import Any

from sqlalchemy import select

from apps.admin.dao.base_dao import _create, _delete, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.website import WebsiteCategory


@Component()
class AdminWebsiteCategoryDao:
    """后台网站导航分类数据访问对象。"""

    async def list_website_categories(self) -> list[WebsiteCategory]:
        """
        查询网站导航分类列表。

        :return: 网站导航分类列表。
        """
        return list(
            await db.model_all(select(WebsiteCategory).order_by(WebsiteCategory.index, WebsiteCategory.id.desc()))
        )

    async def get_website_category_by_id(self, category_id: int) -> WebsiteCategory | None:
        """
        根据 ID 查询网站导航分类。

        :param category_id: 网站导航分类 ID。
        :return: 网站导航分类对象。
        """
        return await db.model_first(select(WebsiteCategory).where(WebsiteCategory.id == category_id))

    async def create_website_category(self, data: dict[str, Any]) -> WebsiteCategory:
        """
        创建网站导航分类。

        :param data: 网站导航分类数据。
        :return: 网站导航分类对象。
        """
        return await _create(WebsiteCategory, data)

    async def update_website_category(self, category: WebsiteCategory, data: dict[str, Any]) -> WebsiteCategory:
        """
        更新网站导航分类。

        :param category: 网站导航分类对象。
        :param data: 更新数据。
        :return: 网站导航分类对象。
        """
        return await _update(category, data)

    async def delete_website_category(self, category_id: int) -> None:
        """
        删除网站导航分类。

        :param category_id: 网站导航分类 ID。
        :return: None。
        """
        await _delete(WebsiteCategory, category_id)
