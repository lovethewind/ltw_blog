from sqlalchemy import select

from apps.admin.core.context_vars import AdminContextVars
from apps.admin.dao.menu_dao import AdminMenuDao
from apps.admin.dto.menu_dto import AdminMenuDTO, AdminRoleDTO
from apps.admin.vo.menu_vo import (
    AdminMenuCreateVO,
    AdminMenuUpdateVO,
    AdminRoleCreateVO,
    AdminRoleMenuUpdateVO,
    AdminRoleUpdateVO,
)
from apps.base.core.depend_inject import Autowired, Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.error_code import ErrorCode
from apps.base.enum.user import MenuTypeEnum
from apps.base.exception.my_exception import MyException
from apps.base.models.user import Menu, User


@Component()
class AdminMenuService:
    """
    后台菜单权限服务。
    """

    admin_menu_dao: AdminMenuDao = Autowired()

    async def list_menu_tree(self, active_only: bool = False) -> list[AdminMenuDTO]:
        """
        查询后台菜单树。

        :param active_only: 是否只查询启用菜单
        :return: 菜单树
        """
        menus = await self.admin_menu_dao.list_all_menus(active_only)
        return self._build_manage_menu_tree(menus)

    async def get_menu(self, menu_id: int) -> AdminMenuDTO:
        """
        查询菜单详情。

        :param menu_id: 菜单 ID
        :return: 菜单详情
        :raises MyException: 菜单不存在时抛出
        """
        menu = await self.admin_menu_dao.get_menu_by_id(menu_id)
        if not menu:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminMenuDTO.model_validate(menu)

    async def create_menu(self, menu_vo: AdminMenuCreateVO) -> AdminMenuDTO:
        """
        创建菜单。

        :param menu_vo: 菜单创建参数
        :return: 菜单详情
        """
        data = menu_vo.model_dump(exclude_none=True)
        menu = await self.admin_menu_dao.create_menu(data)
        return AdminMenuDTO.model_validate(menu)

    async def update_menu(self, menu_id: int, menu_vo: AdminMenuUpdateVO) -> AdminMenuDTO:
        """
        更新菜单。

        :param menu_id: 菜单 ID
        :param menu_vo: 菜单更新参数
        :return: 菜单详情
        :raises MyException: 菜单不存在时抛出
        """
        menu = await self.admin_menu_dao.get_menu_by_id(menu_id)
        if not menu:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = menu_vo.model_dump(exclude_none=True)
        if not data:
            return AdminMenuDTO.model_validate(menu)
        menu = await self.admin_menu_dao.update_menu(menu, data)
        return AdminMenuDTO.model_validate(menu)

    async def delete_menu(self, menu_id: int) -> None:
        """
        删除菜单。

        :param menu_id: 菜单 ID
        :return: None
        :raises MyException: 菜单不存在或存在子级时抛出
        """
        menu = await self.admin_menu_dao.get_menu_by_id(menu_id)
        if not menu:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        if await self.admin_menu_dao.has_children(menu_id):
            raise MyException(ErrorCode.MENU_HAS_SUB_ITEM)
        await self.admin_menu_dao.delete_menu(menu_id)

    async def list_roles(self) -> list[AdminRoleDTO]:
        """
        查询角色列表。

        :return: 角色列表
        """
        roles = await self.admin_menu_dao.list_roles()
        return [AdminRoleDTO.model_validate(role) for role in roles]

    async def create_role(self, role_vo: AdminRoleCreateVO) -> AdminRoleDTO:
        """
        创建角色。

        :param role_vo: 角色创建参数
        :return: 角色详情
        """
        role = await self.admin_menu_dao.create_role(role_vo.model_dump(exclude_none=True))
        return AdminRoleDTO.model_validate(role)

    async def update_role(self, role_id: int, role_vo: AdminRoleUpdateVO) -> AdminRoleDTO:
        """
        更新角色。

        :param role_id: 角色 ID
        :param role_vo: 角色更新参数
        :return: 角色详情
        :raises MyException: 角色不存在时抛出
        """
        role = await self.admin_menu_dao.get_role_by_id(role_id)
        if not role:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = role_vo.model_dump(exclude_none=True)
        if not data:
            return AdminRoleDTO.model_validate(role)
        role = await self.admin_menu_dao.update_role(role, data)
        return AdminRoleDTO.model_validate(role)

    async def delete_role(self, role_id: int) -> None:
        """
        删除角色。

        :param role_id: 角色 ID
        :return: None
        :raises MyException: 角色不存在时抛出
        """
        role = await self.admin_menu_dao.get_role_by_id(role_id)
        if not role:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_menu_dao.delete_role(role_id)

    async def get_role_menu_ids(self, role_id: int) -> list[int]:
        """
        查询角色菜单授权。

        :param role_id: 角色 ID
        :return: 菜单 ID 列表
        :raises MyException: 角色不存在时抛出
        """
        role = await self.admin_menu_dao.get_role_by_id(role_id)
        if not role:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return await self.admin_menu_dao.get_role_menu_ids(role_id)

    async def update_role_menus(self, role_id: int, role_menu_vo: AdminRoleMenuUpdateVO) -> None:
        """
        更新角色菜单授权。

        :param role_id: 角色 ID
        :param role_menu_vo: 角色菜单授权参数
        :return: None
        :raises MyException: 角色不存在时抛出
        """
        role = await self.admin_menu_dao.get_role_by_id(role_id)
        if not role:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_menu_dao.update_role_menus(role_id, role_menu_vo.menu_ids)

    async def get_current_route_menus(self, user: User) -> list[dict]:
        """
        查询当前用户可访问路由菜单。

        :param user: 当前用户
        :return: Vben 路由菜单
        """
        menus = await self._get_user_menus(user, active_only=True)
        route_menus = [menu for menu in menus if menu.menu_type != MenuTypeEnum.BUTTON]
        return self._build_route_menu_tree(route_menus)

    async def get_current_button_codes(self) -> list[str]:
        """
        查询当前用户按钮权限码。

        :return: 按钮权限码列表
        :raises MyException: 用户不存在时抛出
        """
        user_id = AdminContextVars.token_user_id.get()
        if not user_id:
            raise MyException(ErrorCode.ACCOUNT_NOT_EXIST)

        user = await db.model_first(select(User).where(User.id == user_id))
        if not user:
            raise MyException(ErrorCode.ACCOUNT_NOT_EXIST)
        menus = await self._get_user_menus(user, active_only=True)
        return [menu.code for menu in menus if menu.menu_type == MenuTypeEnum.BUTTON]

    async def _get_user_menus(self, user: User, active_only: bool = True) -> list[Menu]:
        """
        查询用户菜单集合。

        :param user: 用户对象
        :param active_only: 是否只查询启用菜单
        :return: 菜单列表
        """
        role_ids = await self.admin_menu_dao.get_user_role_ids(user.id)
        return await self.admin_menu_dao.list_role_menus(role_ids, active_only)

    def _build_manage_menu_tree(self, menus: list[Menu]) -> list[AdminMenuDTO]:
        """
        构建后台管理菜单树。

        :param menus: 菜单列表
        :return: 菜单树
        """
        node_map = {menu.id: AdminMenuDTO.model_validate(menu) for menu in menus}
        for node in node_map.values():
            node.children = []
        roots = []
        for menu in menus:
            node = node_map[menu.id]
            parent_node = node_map.get(menu.parent_id)
            if parent_node:
                parent_node.children.append(node)
            else:
                roots.append(node)
        return roots

    def _build_route_menu_tree(self, menus: list[Menu]) -> list[dict]:
        """
        构建 Vben 路由菜单树。

        :param menus: 菜单列表
        :return: 路由菜单树
        """
        node_map = {menu.id: self._to_route_menu(menu) for menu in menus}
        for node in node_map.values():
            node["children"] = []
        roots = []
        for menu in menus:
            node = node_map[menu.id]
            parent_node = node_map.get(menu.parent_id)
            if parent_node:
                parent_node["children"].append(node)
            else:
                roots.append(node)
        return self._drop_empty_children(roots)

    def _to_route_menu(self, menu: Menu) -> dict:
        """
        转换为 Vben 路由菜单节点。

        :param menu: 菜单对象
        :return: 路由菜单节点
        """
        node = {
            "name": menu.route_name or menu.code,
            "path": menu.path,
            "meta": {
                "hideInMenu": menu.hidden,
                "icon": menu.icon,
                "order": menu.index,
                "title": menu.name,
            },
        }
        if menu.component:
            node["component"] = menu.component
        if menu.always_show:
            node["meta"]["alwaysShow"] = True
        if menu.is_out_link:
            node["meta"]["link"] = menu.path
        return node

    def _drop_empty_children(self, nodes: list[dict]) -> list[dict]:
        """
        移除空 children 字段。

        :param nodes: 菜单节点列表
        :return: 菜单节点列表
        """
        for node in nodes:
            children = node.get("children") or []
            if children:
                self._drop_empty_children(children)
            else:
                node.pop("children", None)
        return nodes
