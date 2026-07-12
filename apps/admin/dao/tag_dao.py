from typing import Any

from sqlalchemy import func, select

from apps.admin.dao.base_dao import _create, _delete, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.category import Tag


@Component()
class AdminTagDao:
    """后台标签数据访问对象。"""

    async def list_tags(self, active_only: bool = False) -> list[Tag]:
        """
        查询标签列表。

        :param active_only: 是否只查询启用标签。
        :return: 标签列表。
        """
        stmt = select(Tag)
        if active_only:
            stmt = stmt.where(Tag.is_active.is_(True))
        return list(await db.model_all(stmt.order_by(Tag.index, Tag.id.desc())))

    async def get_tag_by_id(self, tag_id: int) -> Tag | None:
        """
        根据 ID 查询标签。

        :param tag_id: 标签 ID。
        :return: 标签对象。
        """
        return await db.model_first(select(Tag).where(Tag.id == tag_id))

    async def create_tag(self, data: dict[str, Any]) -> Tag:
        """
        创建标签。

        :param data: 标签数据。
        :return: 标签对象。
        """
        return await _create(Tag, data)

    async def update_tag(self, tag: Tag, data: dict[str, Any]) -> Tag:
        """
        更新标签。

        :param tag: 标签对象。
        :param data: 更新数据。
        :return: 标签对象。
        """
        return await _update(tag, data)

    async def delete_tag(self, tag_id: int) -> None:
        """
        删除标签。

        :param tag_id: 标签 ID。
        :return: None。
        """
        await _delete(Tag, tag_id)

    async def has_tag_children(self, tag_id: int) -> bool:
        """
        判断标签是否存在子级。

        :param tag_id: 标签 ID。
        :return: 是否存在子级。
        """
        return bool(await db.scalar(select(func.count(Tag.id)).where(Tag.parent_id == tag_id)))
