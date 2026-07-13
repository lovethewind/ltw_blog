from typing import Any

from sqlalchemy import delete, func, select, update

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.user import Menu, Role, RoleMenu, UserRole


@Component()
class AdminMenuDao:
    """
    后台菜单数据访问对象。
    """

    async def list_all_menus(self, active_only: bool = False) -> list[Menu]:
        """
        查询全部菜单。

        :param active_only: 是否只查询启用菜单。
        :return: 菜单列表。
        """
        stmt = select(Menu)
        if active_only:
            stmt = stmt.where(Menu.is_active.is_(True))
        return list(await db.model_all(stmt.order_by(Menu.index, Menu.id)))

    async def list_role_menus(self, role_ids: list[int], active_only: bool = False) -> list[Menu]:
        """
        查询角色拥有的菜单。

        :param role_ids: 角色 ID 列表。
        :param active_only: 是否只查询启用菜单。
        :return: 菜单列表。
        """
        if not role_ids:
            return []
        menu_ids = await db.model_all(select(RoleMenu.menu_id).where(RoleMenu.role_id.in_(role_ids)))
        if not menu_ids:
            return []
        stmt = select(Menu).where(Menu.id.in_(menu_ids))
        if active_only:
            stmt = stmt.where(Menu.is_active.is_(True))
        return list(await db.model_all(stmt.order_by(Menu.index, Menu.id)))

    async def get_user_role_ids(self, user_id: int) -> list[int]:
        """
        查询用户角色 ID 列表。

        :param user_id: 用户 ID。
        :return: 角色 ID 列表。
        """
        return list(await db.model_all(select(UserRole.role_id).where(UserRole.user_id == user_id)))

    async def get_menu_by_id(self, menu_id: int) -> Menu | None:
        """
        根据 ID 查询菜单。

        :param menu_id: 菜单 ID。
        :return: 菜单对象。
        """
        return await db.model_first(select(Menu).where(Menu.id == menu_id))

    async def create_menu(self, data: dict[str, Any]) -> Menu:
        """
        创建菜单。

        :param data: 菜单数据。
        :return: 菜单对象。
        """
        menu = Menu(**data)
        async with db.atomic() as session:
            session.add(menu)
            await session.flush()
            await session.refresh(menu)
        return menu

    async def update_menu(self, menu: Menu, data: dict[str, Any]) -> Menu:
        """
        更新菜单。

        :param menu: 菜单对象。
        :param data: 更新数据。
        :return: 菜单对象。
        """
        if not data:
            return menu
        for key, value in data.items():
            setattr(menu, key, value)
        await db.execute(update(Menu).where(Menu.id == menu.id).values(**data))
        return menu

    async def has_children(self, menu_id: int) -> bool:
        """
        判断菜单是否存在子级。

        :param menu_id: 菜单 ID。
        :return: 是否存在子级。
        """
        return bool(await db.scalar(select(func.count(Menu.id)).where(Menu.parent_id == menu_id)))

    async def list_child_ids(self, parent_id: int) -> list[int]:
        """
        查询直接子菜单 ID 列表。

        :param parent_id: 父菜单 ID。
        :return: 直接子菜单 ID 列表。
        """
        return list(await db.model_all(select(Menu.id).where(Menu.parent_id == parent_id)))

    async def delete_menu(self, menu_id: int) -> None:
        """
        删除菜单及角色菜单关联。

        :param menu_id: 菜单 ID。
        :return: None。
        """
        async with db.atomic() as session:
            await session.execute(delete(RoleMenu).where(RoleMenu.menu_id == menu_id))
            await session.execute(delete(Menu).where(Menu.id == menu_id))

    async def delete_menus(self, menu_ids: list[int]) -> None:
        """
        在同一事务中删除菜单及角色菜单关联。

        :param menu_ids: 待删除菜单 ID 列表。
        :return: None。
        """
        if not menu_ids:
            return
        async with db.atomic() as session:
            await session.execute(delete(RoleMenu).where(RoleMenu.menu_id.in_(menu_ids)))
            await session.execute(delete(Menu).where(Menu.id.in_(menu_ids)))

    async def list_roles(self) -> list[Role]:
        """
        查询角色列表。

        :return: 角色列表。
        """
        return list(await db.model_all(select(Role).order_by(Role.id)))

    async def get_role_by_id(self, role_id: int) -> Role | None:
        """
        根据 ID 查询角色。

        :param role_id: 角色 ID。
        :return: 角色对象。
        """
        return await db.model_first(select(Role).where(Role.id == role_id))

    async def create_role(self, data: dict[str, Any]) -> Role:
        """
        创建角色。

        :param data: 角色数据。
        :return: 角色对象。
        """
        role = Role(**data)
        async with db.atomic() as session:
            session.add(role)
            await session.flush()
            await session.refresh(role)
        return role

    async def update_role(self, role: Role, data: dict[str, Any]) -> Role:
        """
        更新角色。

        :param role: 角色对象。
        :param data: 更新数据。
        :return: 角色对象。
        """
        if not data:
            return role
        for key, value in data.items():
            setattr(role, key, value)
        await db.execute(update(Role).where(Role.id == role.id).values(**data))
        return role

    async def delete_role(self, role_id: int) -> None:
        """
        删除角色及关联。

        :param role_id: 角色 ID。
        :return: None。
        """
        async with db.atomic() as session:
            await session.execute(delete(RoleMenu).where(RoleMenu.role_id == role_id))
            await session.execute(delete(UserRole).where(UserRole.role_id == role_id))
            await session.execute(delete(Role).where(Role.id == role_id))

    async def get_role_menu_ids(self, role_id: int) -> list[int]:
        """
        查询角色菜单 ID 列表。

        :param role_id: 角色 ID。
        :return: 菜单 ID 列表。
        """
        return list(await db.model_all(select(RoleMenu.menu_id).where(RoleMenu.role_id == role_id)))

    async def update_role_menus(self, role_id: int, menu_ids: list[int]) -> None:
        """
        更新角色菜单授权。

        :param role_id: 角色 ID。
        :param menu_ids: 菜单 ID 列表。
        :return: None。
        """
        async with db.atomic() as session:
            await session.execute(delete(RoleMenu).where(RoleMenu.role_id == role_id))
            session.add_all([RoleMenu(role_id=role_id, menu_id=menu_id) for menu_id in set(menu_ids)])
