# @Time    : 2024/11/4 13:56
# @Author  : frank
# @File    : chat_controller.py
from fastapi import APIRouter, Depends

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.enum.chat import ContactApplyStatusEnum, ContactTypeEnum
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.chat_service import ChatService
from apps.web.vo.chat_vo import ConversationVO, HistoryMessageVO, ConversationUpdateVO, ContactApplyVO, \
    HandleContactApplyVO, ContactVO

router = APIRouter(prefix="/chat", tags=["聊天模块"])


@Controller(router)
class ChatController:
    chat_service: ChatService = Autowired()

    @router.get("/conversation/{current_page}/{page_size}", summary="获取会话列表")
    async def list_conversation(self, current_page: int, page_size: int):
        """
        获取会话列表
        :param current_page:
        :param page_size:
        :return:
        """
        ret = await self.chat_service.list_conversation(current_page, page_size)
        return ResponseUtil.success(ret)

    @router.get("/conversationDetail", summary="获取会话详情")
    async def get_conversation_detail(self, conversation_vo: ConversationVO = Depends()):
        """
        获取会话详情
        :param conversation_vo:
        :return:
        """
        ret = await self.chat_service.get_conversation_detail(conversation_vo)
        return ResponseUtil.success(ret)

    @router.put("/conversation", summary="更新会话信息")
    async def update_conversation(self, conversation_update_vo: ConversationUpdateVO):
        """
        更新会话信息
        :param conversation_update_vo:
        :return:
        """
        await self.chat_service.update_conversation(conversation_update_vo)
        return ResponseUtil.success()

    @router.get("/message", summary="获取消息列表")
    async def list_message(self, history_message_vo: HistoryMessageVO = Depends()):
        """
        获取消息列表
        :param history_message_vo:
        :return:
        """
        ret = await self.chat_service.list_message(history_message_vo)
        return ResponseUtil.success(ret)

    @router.post("/contactApply", summary="添加好友申请")
    async def contact_apply(self, contact_apply_vo: ContactApplyVO):
        """
        添加好友申请
        :param contact_apply_vo:
        :return:
        """
        await self.chat_service.contact_apply(contact_apply_vo)
        return ResponseUtil.success()

    @router.get("/listContactApply", summary="获取好友申请列表")
    async def list_contact_apply(self):
        """
        获取好友申请列表
        :return:
        """
        ret = await self.chat_service.list_contact_apply()
        return ResponseUtil.success(ret)

    @router.put("/contactApply", summary="处理好友申请")
    async def handle_contact_apply(self, handle_contact_apply_vo: HandleContactApplyVO):
        """
        处理好友申请
        :param handle_contact_apply_vo:
        :return:
        """
        await self.chat_service.handle_contact_apply(handle_contact_apply_vo)
        return ResponseUtil.success()

    @router.get("/contact/{contact_type}/{current_page}/{page_size}", summary="获取好友列表")
    async def list_contact(self, contact_type: ContactTypeEnum, current_page: int, page_size: int):
        """
        获取好友列表
        :param contact_type:
        :param current_page:
        :param page_size:
        :return:
        """
        ret = await self.chat_service.list_contact(contact_type, current_page, page_size)
        return ResponseUtil.success(ret)

    @router.delete("/contact", summary="删除好友")
    async def delete_contact(self, contact_vo: ContactVO):
        """
        删除好友
        :param contact_vo:
        :return:
        """
        ret = await self.chat_service.delete_contact(contact_vo)
        return ResponseUtil.success(ret)