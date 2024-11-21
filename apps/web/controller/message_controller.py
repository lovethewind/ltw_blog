# @Time    : 2024/9/4 16:42
# @Author  : frank
# @File    : message_controller.py
from fastapi import APIRouter
from fastapi.params import Depends

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.message_service import MessageService
from apps.web.vo.message_vo import MessageAddVO

router = APIRouter(prefix="/message", tags=["留言模块"])


@Controller(router)
class MessageController:
    message_service: MessageService = Autowired()

    @router.get("/common/{current}/{size}", summary="获取留言板")
    async def list_messages(self, current: int, size: int):
        """
        获取留言板
        :param current:
        :param size:
        :return:
        """
        ret = await self.message_service.list_messages(current, size)
        return ResponseUtil.success(ret)

    @router.get("/common/children/{message_id}/{current}/{size}", summary="获取留言的子留言")
    async def list_children_message(self, message_id: int, current: int, size: int):
        """
        获取留言的子留言
        :param message_id:
        :param current:
        :param size:
        :return:
        """
        ret = await self.message_service.list_children_message(message_id, current, size)
        return ResponseUtil.success(ret)

    @router.post("/common/add", summary="添加留言")
    async def add(self, message_add_vo: MessageAddVO):
        """
        添加留言
        :param message_add_vo:
        :return:
        """
        ret = await self.message_service.add(message_add_vo)
        return ResponseUtil.success(ret)
