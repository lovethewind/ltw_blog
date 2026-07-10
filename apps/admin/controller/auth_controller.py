from fastapi import Body
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.auth_service import AdminAuthService
from apps.admin.vo.auth_vo import AdminLoginVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/auth", tags=["后台认证"])


@Controller(router)
class AdminAuthController:
    """
    后台认证控制器。
    """

    admin_auth_service: AdminAuthService = Autowired()

    @router.post("/login", summary="后台登录")
    async def login(self, login_vo: AdminLoginVO = Body()) -> Response:
        """
        后台管理员登录。

        :param login_vo: 后台登录参数
        :return: 登录结果
        """
        ret = await self.admin_auth_service.login(login_vo)
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
        ret = await self.admin_auth_service.codes()
        return ResponseUtil.success(ret)
