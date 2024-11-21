# @Time    : 2024/8/28 11:19
# @Author  : frank
# @File    : comment_controller.py
from fastapi import APIRouter, Depends

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.comment_service import CommentService
from apps.web.vo.comment_vo import CommentQueryVO, CommentAddVO

router = APIRouter(prefix="/comment", tags=["评论模块"])


@Controller(router)
class CommentController:
    comment_service: CommentService = Autowired()

    @router.get("/common/{current}/{size}", summary="获取评论")
    async def list_comments(self, current: int, size: int, comment_query_vo: CommentQueryVO = Depends()):
        """
        获取评论
        :param current: 当前页
        :param size: 每页大小
        :param comment_query_vo: CommentQueryVO
        :return:
        """
        ret = await self.comment_service.list_comments(current, size, comment_query_vo)
        return ResponseUtil.success(ret)

    @router.get("/common/children/{comment_id}/{current}/{size}", summary="获取评论的子评论")
    async def list_children_comment(self, comment_id: int, current: int, size: int):
        """
        获取评论的子评论
        :param comment_id:
        :param current:
        :param size:
        :return:
        """
        ret = await self.comment_service.list_children_comment(comment_id, current, size)
        return ResponseUtil.success(ret)

    @router.post("/add", summary="添加评论")
    async def add(self, comment_add_vo: CommentAddVO):
        """
        添加评论
        :param comment_add_vo:
        :return:
        """
        ret = await self.comment_service.add(comment_add_vo)
        return ResponseUtil.success(ret)

    @router.delete("/delete/{comment_id}", summary="删除评论")
    async def delete(self, comment_id: int):
        """
        根据评论id删除评论
        :param comment_id:
        :return:
        """
        await self.comment_service.delete(comment_id)
        return ResponseUtil.success()
