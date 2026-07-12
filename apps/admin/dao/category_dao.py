from typing import Any

from sqlalchemy import select

from apps.admin.dao.base_dao import _create, _delete, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.category import Category


@Component()
class AdminCategoryDao:
    """后台分类数据访问对象。"""

    async def list_categories(self) -> list[Category]:
        """
        查询分类列表。

        :return: 分类列表。
        """
        return list(await db.model_all(select(Category).order_by(Category.index, Category.id.desc())))

    async def get_category_by_id(self, category_id: int) -> Category | None:
        """
        根据 ID 查询分类。

        :param category_id: 分类 ID。
        :return: 分类对象。
        """
        return await db.model_first(select(Category).where(Category.id == category_id))

    async def create_category(self, data: dict[str, Any]) -> Category:
        """
        创建分类。

        :param data: 分类数据。
        :return: 分类对象。
        """
        return await _create(Category, data)

    async def update_category(self, category: Category, data: dict[str, Any]) -> Category:
        """
        更新分类。

        :param category: 分类对象。
        :param data: 更新数据。
        :return: 分类对象。
        """
        return await _update(category, data)

    async def delete_category(self, category_id: int) -> None:
        """
        删除分类。

        :param category_id: 分类 ID。
        :return: None。
        """
        await _delete(Category, category_id)
