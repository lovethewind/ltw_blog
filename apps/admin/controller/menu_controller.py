from fastapi import Body
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.menu_service import AdminMenuService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.menu_vo import (
    AdminMenuCreateVO,
    AdminMenuUpdateVO,
    AdminRoleCreateVO,
    AdminRoleMenuUpdateVO,
    AdminRoleUpdateVO,
)
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/menu", tags=["后台菜单权限"])


@Controller(router)
class AdminMenuController:
    """
    后台菜单权限控制器。
    """

    admin_menu_service: AdminMenuService = Autowired()

    @router.get("/tree", summary="查询后台菜单树")
    @permission("menu:query")
    async def tree(self, active_only: bool = False) -> Response:
        """
        查询后台菜单树。

        :param active_only: 是否只查询启用菜单
        :return: 菜单树
        """
        ret = await self.admin_menu_service.list_menu_tree(active_only)
        return ResponseUtil.success(ret)

    @router.get("/role/list", summary="查询后台角色列表")
    @permission("role:query")
    async def list_roles(self) -> Response:
        """
        查询后台角色列表。

        :return: 角色列表
        """
        ret = await self.admin_menu_service.list_roles()
        return ResponseUtil.success(ret)

    @router.post("/role", summary="创建后台角色")
    @permission("role:create")
    async def create_role(self, role_vo: AdminRoleCreateVO = Body()) -> Response:
        """
        创建后台角色。

        :param role_vo: 角色创建参数
        :return: 角色详情
        """
        ret = await self.admin_menu_service.create_role(role_vo)
        return ResponseUtil.success(ret)

    @router.put("/role/{role_id}", summary="更新后台角色")
    @permission("role:update")
    async def update_role(self, role_id: int, role_vo: AdminRoleUpdateVO = Body()) -> Response:
        """
        更新后台角色。

        :param role_id: 角色 ID
        :param role_vo: 角色更新参数
        :return: 角色详情
        """
        ret = await self.admin_menu_service.update_role(role_id, role_vo)
        return ResponseUtil.success(ret)

    @router.delete("/role/{role_id}", summary="删除后台角色")
    @permission("role:delete")
    async def delete_role(self, role_id: int) -> Response:
        """
        删除后台角色。

        :param role_id: 角色 ID
        :return: 删除结果
        """
        await self.admin_menu_service.delete_role(role_id)
        return ResponseUtil.success()

    @router.get("/role/{role_id}/menus", summary="查询角色菜单授权")
    @permission("role:auth")
    async def get_role_menu_ids(self, role_id: int) -> Response:
        """
        查询角色菜单授权。

        :param role_id: 角色 ID
        :return: 菜单 ID 列表
        """
        ret = await self.admin_menu_service.get_role_menu_ids(role_id)
        return ResponseUtil.success(ret)

    @router.put("/role/{role_id}/menus", summary="更新角色菜单授权")
    @permission("role:auth")
    async def update_role_menus(self, role_id: int, role_menu_vo: AdminRoleMenuUpdateVO = Body()) -> Response:
        """
        更新角色菜单授权。

        :param role_id: 角色 ID
        :param role_menu_vo: 角色菜单授权参数
        :return: 更新结果
        """
        await self.admin_menu_service.update_role_menus(role_id, role_menu_vo)
        return ResponseUtil.success()

    @router.get("/{menu_id}", summary="查询后台菜单详情")
    @permission("menu:query")
    async def get_menu(self, menu_id: int) -> Response:
        """
        查询后台菜单详情。

        :param menu_id: 菜单 ID
        :return: 菜单详情
        """
        ret = await self.admin_menu_service.get_menu(menu_id)
        return ResponseUtil.success(ret)

    @router.post("/", summary="创建后台菜单")
    @permission("menu:create")
    async def create_menu(self, menu_vo: AdminMenuCreateVO = Body()) -> Response:
        """
        创建后台菜单。

        :param menu_vo: 菜单创建参数
        :return: 菜单详情
        """
        ret = await self.admin_menu_service.create_menu(menu_vo)
        return ResponseUtil.success(ret)

    @router.put("/{menu_id}", summary="更新后台菜单")
    @permission("menu:update")
    async def update_menu(self, menu_id: int, menu_vo: AdminMenuUpdateVO = Body()) -> Response:
        """
        更新后台菜单。

        :param menu_id: 菜单 ID
        :param menu_vo: 菜单更新参数
        :return: 菜单详情
        """
        ret = await self.admin_menu_service.update_menu(menu_id, menu_vo)
        return ResponseUtil.success(ret)

    @router.delete("/{menu_id}", summary="删除后台菜单")
    @permission("menu:delete")
    async def delete_menu(self, menu_id: int) -> Response:
        """
        删除后台菜单。

        :param menu_id: 菜单 ID
        :return: 删除结果
        """
        await self.admin_menu_service.delete_menu(menu_id)
        return ResponseUtil.success()
