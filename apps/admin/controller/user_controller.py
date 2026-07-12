from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.user_service import AdminUserService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.user_vo import (
    AdminLoginVO,
    AdminUserCreateVO,
    AdminUserQueryVO,
    AdminUserRoleUpdateVO,
    AdminUserUpdateVO,
)
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/user", tags=["后台用户信息"])


@Controller(router)
class AdminUserController:
    """
    后台用户信息控制器。
    """

    admin_user_service: AdminUserService = Autowired()

    @router.post("/login", summary="后台登录")
    async def login(self, login_vo: AdminLoginVO = Body()) -> Response:
        """
        后台管理员登录。

        :param login_vo: 后台登录参数
        :return: 登录结果
        """
        ret = await self.admin_user_service.login(login_vo)
        return ResponseUtil.success(ret)

    @router.post("/logout", summary="后台退出登录")
    async def logout(self) -> Response:
        """
        后台管理员退出登录。

        :return: 退出登录结果
        """
        return ResponseUtil.success()

    @router.get("/codes", summary="获取后台权限码")
    async def codes(self) -> Response:
        """
        获取当前后台管理员权限码。

        :return: 权限码列表
        """
        ret = await self.admin_user_service.codes()
        return ResponseUtil.success(ret)

    @router.get("/info", summary="获取后台当前用户信息")
    async def info(self) -> Response:
        """
        根据后台 token 获取当前管理员信息。

        :return: 当前管理员信息
        """
        ret = await self.admin_user_service.info()
        return ResponseUtil.success(ret)

    @router.get("/menus", summary="获取后台菜单")
    async def menus(self) -> Response:
        """
        获取当前管理员可访问菜单。

        :return: 菜单列表
        """
        ret = await self.admin_user_service.menus()
        return ResponseUtil.success(ret)

    @router.get("/list", summary="分页查询后台用户")
    @permission("system:user:query")
    async def list_users(self, query_vo: AdminUserQueryVO = Depends()) -> Response:
        """
        分页查询后台用户。

        :param query_vo: 用户查询参数
        :return: 用户分页数据
        """
        ret = await self.admin_user_service.list_users(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/{user_id}", summary="获取后台用户详情")
    @permission("system:user:query")
    async def get_user(self, user_id: int) -> Response:
        """
        获取后台用户详情。

        :param user_id: 用户 ID
        :return: 用户详情
        """
        ret = await self.admin_user_service.get_user(user_id)
        return ResponseUtil.success(ret)

    @router.post("/", summary="创建后台用户")
    @permission("system:user:create")
    async def create_user(self, user_vo: AdminUserCreateVO = Body()) -> Response:
        """
        创建后台用户。

        :param user_vo: 用户创建参数
        :return: 用户详情
        """
        ret = await self.admin_user_service.create_user(user_vo)
        return ResponseUtil.success(ret)

    @router.put("/{user_id}", summary="更新后台用户")
    @permission("system:user:update")
    async def update_user(self, user_id: int, user_vo: AdminUserUpdateVO = Body()) -> Response:
        """
        更新后台用户。

        :param user_id: 用户 ID
        :param user_vo: 用户更新参数
        :return: 用户详情
        """
        ret = await self.admin_user_service.update_user(user_id, user_vo)
        return ResponseUtil.success(ret)

    @router.delete("/{user_id}", summary="删除后台用户")
    @permission("system:user:delete")
    async def delete_user(self, user_id: int) -> Response:
        """
        删除后台用户。

        :param user_id: 用户 ID
        :return: None
        """
        await self.admin_user_service.delete_user(user_id)
        return ResponseUtil.success()

    @router.get("/{user_id}/roles", summary="获取后台用户角色")
    @permission("system:user:role")
    async def get_user_role_ids(self, user_id: int) -> Response:
        """
        获取后台用户角色。

        :param user_id: 用户 ID
        :return: 角色 ID 列表
        """
        ret = await self.admin_user_service.get_user_role_ids(user_id)
        return ResponseUtil.success(ret)

    @router.put("/{user_id}/roles", summary="更新后台用户角色")
    @permission("system:user:role")
    async def update_user_roles(self, user_id: int, user_role_vo: AdminUserRoleUpdateVO = Body()) -> Response:
        """
        更新后台用户角色。

        :param user_id: 用户 ID
        :param user_role_vo: 用户角色参数
        :return: None
        """
        await self.admin_user_service.update_user_roles(user_id, user_role_vo)
        return ResponseUtil.success()
