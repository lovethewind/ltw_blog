# @Time    : 2024/10/21 16:19
# @Author  : frank
# @File    : notice_controller.py
from fastapi import APIRouter

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.enum.notice import NoticeTypeEnum
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.notice_service import NoticeService
from apps.web.vo.batch_vo import BatchVO

router = APIRouter(prefix="/notice", tags=["消息模块"])


@Controller(router)
class NoticeController:
    notice_service: NoticeService = Autowired()

    @router.get("/getUnreadCount", summary="获取各类消息未读数量")
    async def get_unread_notice_count(self):
        """
        获取各类消息未读数量
        :return:
        """
        ret = await self.notice_service.get_unread_notice_count()
        return ResponseUtil.success(ret)

    @router.get("/list/{notice_type}/{current}/{size}", summary="获取消息列表")
    async def list_notice(self, notice_type: NoticeTypeEnum, current: int, size: int):
        """
        获取消息列表
        :param notice_type: 消息类型
        :param current: 当前页
        :param size: 每页条数
        :return:
        """
        ret = await self.notice_service.get_notice_list(notice_type, current, size)
        return ResponseUtil.success(ret)

    @router.put("/update", summary="更新消息为已读")
    async def update(self, batch_vo: BatchVO):
        """
        更新消息为已读
        :param batch_vo:
        :return:
        """
        await self.notice_service.update(batch_vo)
        return ResponseUtil.success()

    @router.delete("/delete", summary="删除消息")
    async def delete(self, batch_vo: BatchVO):
        """
        删除消息
        :param batch_vo:
        :return:
        """
        await self.notice_service.delete(batch_vo)
        return ResponseUtil.success()

    @router.get("/clear/{notice_type}")
    async def clear_notice(self, notice_type: NoticeTypeEnum):
        """
        清空消息
        :param notice_type: 消息类型
        :return:
        """
        await self.notice_service.clear_notice(notice_type)
        return ResponseUtil.success()