from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.message_service import AdminMessageService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.message_vo import AdminMessageQueryVO, AdminMessageUpdateVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/message", tags=["后台留言管理"])


@Controller(router)
class AdminMessageController:
    """后台留言控制器。"""

    admin_message_service: AdminMessageService = Autowired()

    @router.get("/list", summary="分页查询留言")
    @permission("message:query")
    async def list_messages(self, query_vo: AdminMessageQueryVO = Depends()) -> Response:
        """
        分页查询留言。

        :param query_vo: 留言查询参数
        :return: 留言分页数据
        """
        ret = await self.admin_message_service.list_messages(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/{message_id}", summary="查询留言详情")
    @permission("message:query")
    async def get_message(self, message_id: int) -> Response:
        """
        查询留言详情。

        :param message_id: 留言 ID
        :return: 留言详情
        """
        ret = await self.admin_message_service.get_message(message_id)
        return ResponseUtil.success(ret)

    @router.put("/{message_id}", summary="更新留言")
    @permission("message:update")
    async def update_message(self, message_id: int, message_vo: AdminMessageUpdateVO = Body()) -> Response:
        """
        更新留言。

        :param message_id: 留言 ID
        :param message_vo: 留言更新参数
        :return: 留言详情
        """
        ret = await self.admin_message_service.update_message(message_id, message_vo)
        return ResponseUtil.success(ret)

    @router.delete("/{message_id}", summary="删除留言")
    @permission("message:delete")
    async def delete_message(self, message_id: int) -> Response:
        """
        删除留言。

        :param message_id: 留言 ID
        :return: 删除结果
        """
        await self.admin_message_service.delete_message(message_id)
        return ResponseUtil.success()
