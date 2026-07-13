from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.notice_service import AdminNoticeService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.notice_vo import AdminNoticeQueryVO, AdminNoticeUpdateVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/notice", tags=["后台通知管理"])


@Controller(router)
class AdminNoticeController:
    """后台通知控制器。"""

    admin_notice_service: AdminNoticeService = Autowired()

    @router.get("/list", summary="分页查询通知")
    @permission("notice:query")
    async def list_notices(self, query_vo: AdminNoticeQueryVO = Depends()) -> Response:
        """
        分页查询通知。

        :param query_vo: 通知查询参数
        :return: 通知分页数据
        """
        ret = await self.admin_notice_service.list_notices(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/{notice_id}", summary="查询通知详情")
    @permission("notice:query")
    async def get_notice(self, notice_id: int) -> Response:
        """
        查询通知详情。

        :param notice_id: 通知 ID
        :return: 通知详情
        """
        ret = await self.admin_notice_service.get_notice(notice_id)
        return ResponseUtil.success(ret)

    @router.put("/{notice_id}", summary="更新通知")
    @permission("notice:update")
    async def update_notice(self, notice_id: int, notice_vo: AdminNoticeUpdateVO = Body()) -> Response:
        """
        更新通知。

        :param notice_id: 通知 ID
        :param notice_vo: 通知更新参数
        :return: 通知详情
        """
        ret = await self.admin_notice_service.update_notice(notice_id, notice_vo)
        return ResponseUtil.success(ret)

    @router.delete("/{notice_id}", summary="删除通知")
    @permission("notice:delete")
    async def delete_notice(self, notice_id: int) -> Response:
        """
        删除通知。

        :param notice_id: 通知 ID
        :return: 删除结果
        """
        await self.admin_notice_service.delete_notice(notice_id)
        return ResponseUtil.success()
