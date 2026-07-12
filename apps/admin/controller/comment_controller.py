from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.comment_service import AdminCommentService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.comment_vo import AdminCommentQueryVO, AdminCommentStatusVO, AdminCommentUpdateVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/content", tags=["后台内容管理"])


@Controller(router)
class AdminCommentController:
    """后台评论控制器。"""

    admin_comment_service: AdminCommentService = Autowired()

    @router.get("/comment/list", summary="分页查询评论")
    @permission("content:comment:query")
    async def list_comments(self, query_vo: AdminCommentQueryVO = Depends()) -> Response:
        """
        分页查询评论。

        :param query_vo: 评论查询参数
        :return: 评论分页数据
        """
        ret = await self.admin_comment_service.list_comments(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/comment/{comment_id}", summary="查询评论详情")
    @permission("content:comment:query")
    async def get_comment(self, comment_id: int) -> Response:
        """
        查询评论详情。

        :param comment_id: 评论 ID
        :return: 评论详情
        """
        ret = await self.admin_comment_service.get_comment(comment_id)
        return ResponseUtil.success(ret)

    @router.put("/comment/{comment_id}", summary="更新评论")
    @permission("content:comment:update")
    async def update_comment(self, comment_id: int, comment_vo: AdminCommentUpdateVO = Body()) -> Response:
        """
        更新评论。

        :param comment_id: 评论 ID
        :param comment_vo: 评论更新参数
        :return: 评论详情
        """
        ret = await self.admin_comment_service.update_comment(comment_id, comment_vo)
        return ResponseUtil.success(ret)

    @router.put("/comment/{comment_id}/status", summary="更新评论状态")
    @permission("content:comment:status")
    async def update_comment_status(self, comment_id: int, status_vo: AdminCommentStatusVO = Body()) -> Response:
        """
        更新评论状态。

        :param comment_id: 评论 ID
        :param status_vo: 状态更新参数
        :return: 评论详情
        """
        ret = await self.admin_comment_service.update_comment_status(comment_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/comment/{comment_id}", summary="删除评论")
    @permission("content:comment:delete")
    async def delete_comment(self, comment_id: int) -> Response:
        """
        删除评论。

        :param comment_id: 评论 ID
        :return: 删除结果
        """
        await self.admin_comment_service.delete_comment(comment_id)
        return ResponseUtil.success()
