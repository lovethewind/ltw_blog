from typing import Any

from sqlalchemy import select

from apps.admin.dao.base_dao import _create, _delete, _paginate, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.user import UserRestriction


@Component()
class AdminUserRestrictionDao:
    """后台用户限制数据访问对象。"""

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
