from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.user_restriction_service import AdminUserRestrictionService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.user_restriction_vo import (
    AdminUserRestrictionCancelVO,
    AdminUserRestrictionCreateVO,
    AdminUserRestrictionQueryVO,
    AdminUserRestrictionUpdateVO,
)
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/operation", tags=["后台运营管理"])


@Controller(router)
class AdminUserRestrictionController:
    """后台用户限制控制器。"""

    admin_user_restriction_service: AdminUserRestrictionService = Autowired()

    @router.get("/restriction/list", summary="分页查询用户限制")
    @permission("operation:restriction:query")
    async def list_user_restrictions(self, query_vo: AdminUserRestrictionQueryVO = Depends()) -> Response:
        """
        分页查询用户限制。

        :param query_vo: 用户限制查询参数
        :return: 用户限制分页数据
        """
        ret = await self.admin_user_restriction_service.list_user_restrictions(query_vo)
        return ResponseUtil.success(ret)

    @router.post("/restriction", summary="创建用户限制")
    @permission("operation:restriction:create")
    async def create_user_restriction(self, restriction_vo: AdminUserRestrictionCreateVO = Body()) -> Response:
        """
        创建用户限制。

        :param restriction_vo: 用户限制创建参数
        :return: 用户限制详情
        """
        ret = await self.admin_user_restriction_service.create_user_restriction(restriction_vo)
        return ResponseUtil.success(ret)

    @router.put("/restriction/{restriction_id}", summary="更新用户限制")
    @permission("operation:restriction:update")
    async def update_user_restriction(
        self, restriction_id: int, restriction_vo: AdminUserRestrictionUpdateVO = Body()
    ) -> Response:
        """
        更新用户限制。

        :param restriction_id: 用户限制 ID
        :param restriction_vo: 用户限制更新参数
        :return: 用户限制详情
        """
        ret = await self.admin_user_restriction_service.update_user_restriction(restriction_id, restriction_vo)
        return ResponseUtil.success(ret)

    @router.put("/restriction/{restriction_id}/cancel", summary="解除用户限制")
    @permission("operation:restriction:cancel")
    async def cancel_user_restriction(
        self, restriction_id: int, cancel_vo: AdminUserRestrictionCancelVO = Body()
    ) -> Response:
        """
        解除用户限制。

        :param restriction_id: 用户限制 ID
        :param cancel_vo: 解除参数
        :return: 用户限制详情
        """
        ret = await self.admin_user_restriction_service.cancel_user_restriction(restriction_id, cancel_vo)
        return ResponseUtil.success(ret)

    @router.delete("/restriction/{restriction_id}", summary="删除用户限制")
    @permission("operation:restriction:delete")
    async def delete_user_restriction(self, restriction_id: int) -> Response:
        """
        删除用户限制。

        :param restriction_id: 用户限制 ID
        :return: 删除结果
        """
        await self.admin_user_restriction_service.delete_user_restriction(restriction_id)
        return ResponseUtil.success()
