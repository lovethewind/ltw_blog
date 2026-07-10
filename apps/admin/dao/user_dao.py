from typing import Any

from sqlalchemy import delete, exists, func, or_, select, update

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.user import Role, User, UserRole


@Component()
class AdminUserDao:
    """
    后台用户数据访问对象。
    """

    async def get_admin_user_by_username(self, username: str) -> User | None:
        """
        根据用户名获取后台管理员用户。

        :param username: 用户名。
        :return: 管理员用户。
        """
        user = await db.model_first(select(User).where(User.username == username))
        if not user or not await self._has_active_role(user.id):
            return None
        return user

    async def get_admin_user_by_id(self, user_id: int) -> User | None:
        """
        根据用户 ID 获取后台管理员用户。

        :param user_id: 用户 ID。
        :return: 管理员用户。
        """
        user = await db.model_first(select(User).where(User.id == user_id))
        if not user or not await self._has_active_role(user.id):
            return None
        return user

    async def list_users(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
    ) -> tuple[list[User], int]:
        """
        分页查询后台用户列表。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 用户名、昵称、邮箱或手机号关键词。
        :return: 用户列表和总数。
        """
        stmt = select(User)
        if keyword:
            stmt = stmt.where(
                or_(
                    User.username.ilike(f"%{keyword}%"),
                    User.nickname.ilike(f"%{keyword}%"),
                    User.email.ilike(f"%{keyword}%"),
                    User.mobile.ilike(f"%{keyword}%"),
                )
            )
        offset, limit = db.page(current, size)
        total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
        records = await db.model_all(stmt.order_by(User.id.desc()).offset(offset).limit(limit))
        return list(records), int(total or 0)

    async def _has_active_role(self, user_id: int) -> bool:
        """
        判断用户是否绑定启用角色。

        :param user_id: 用户 ID。
        :return: 是否绑定启用角色。
        """
        stmt = (
            select(func.count(Role.id))
            .select_from(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id, Role.is_active.is_(True))
        )
        return bool(await db.scalar(stmt))

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        根据 ID 查询用户。

        :param user_id: 用户 ID。
        :return: 用户对象。
        """
        return await db.model_first(select(User).where(User.id == user_id))

    async def exists_user_field(
        self,
        field: str,
        value: str,
        exclude_user_id: int | None = None,
    ) -> bool:
        """
        判断用户字段值是否已存在。

        :param field: 字段名。
        :param value: 字段值。
        :param exclude_user_id: 排除的用户 ID。
        :return: 是否存在。
        """
        column = getattr(User, field)
        stmt = select(exists().where(column == value))
        if exclude_user_id is not None:
            stmt = select(exists().where(column == value, User.id != exclude_user_id))
        return bool(await db.scalar(stmt))

    async def create_user(self, data: dict[str, Any], role_ids: list[int]) -> User:
        """
        创建用户并保存角色关联。

        :param data: 用户数据。
        :param role_ids: 角色 ID 列表。
        :return: 用户对象。
        """
        user = User(**data)
        async with db.atomic() as session:
            session.add(user)
            await session.flush()
            if role_ids:
                session.add_all([UserRole(user_id=user.id, role_id=role_id) for role_id in set(role_ids)])
            await session.refresh(user)
        return user

    async def update_user(self, user: User, data: dict[str, Any], role_ids: list[int] | None) -> User:
        """
        更新用户并按需保存角色关联。

        :param user: 用户对象。
        :param data: 用户数据。
        :param role_ids: 角色 ID 列表。
        :return: 用户对象。
        """
        async with db.atomic() as session:
            if data:
                for key, value in data.items():
                    setattr(user, key, value)
                await session.execute(update(User).where(User.id == user.id).values(**data))
            if role_ids is not None:
                await session.execute(delete(UserRole).where(UserRole.user_id == user.id))
                if role_ids:
                    session.add_all([UserRole(user_id=user.id, role_id=role_id) for role_id in set(role_ids)])
        return user

    async def delete_user(self, user_id: int) -> None:
        """
        删除用户及用户角色关联。

        :param user_id: 用户 ID。
        :return: None。
        """
        async with db.atomic() as session:
            await session.execute(delete(UserRole).where(UserRole.user_id == user_id))
            await session.execute(delete(User).where(User.id == user_id))

    async def get_user_role_ids(self, user_id: int) -> list[int]:
        """
        查询用户角色 ID 列表。

        :param user_id: 用户 ID。
        :return: 角色 ID 列表。
        """
        return list(await db.model_all(select(UserRole.role_id).where(UserRole.user_id == user_id)))

    async def list_user_role_ids(self, user_ids: list[int]) -> dict[int, list[int]]:
        """
        批量查询用户角色 ID。

        :param user_ids: 用户 ID 列表。
        :return: 用户 ID 到角色 ID 列表的映射。
        """
        if not user_ids:
            return {}
        rows = await db.all(select(UserRole.user_id, UserRole.role_id).where(UserRole.user_id.in_(user_ids)))
        role_map: dict[int, list[int]] = {}
        for row in rows:
            role_map.setdefault(row.user_id, []).append(row.role_id)
        return role_map

    async def update_user_roles(self, user_id: int, role_ids: list[int]) -> None:
        """
        更新用户角色关联。

        :param user_id: 用户 ID。
        :param role_ids: 角色 ID 列表。
        :return: None。
        """
        async with db.atomic() as session:
            await session.execute(delete(UserRole).where(UserRole.user_id == user_id))
            if role_ids:
                session.add_all([UserRole(user_id=user_id, role_id=role_id) for role_id in set(role_ids)])
