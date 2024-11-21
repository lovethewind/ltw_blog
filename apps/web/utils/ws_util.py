# @Time    : 2024/10/24 15:22
# @Author  : frank
# @File    : ws_util.py
import asyncio
from typing import Type, TypeAlias

from fastapi.encoders import jsonable_encoder
from starlette.websockets import WebSocket, WebSocketState
from typing_extensions import TypeVar

from apps.base.core.depend_inject import GetBean
from apps.base.enum.chat import ContactTypeEnum, WSMessageTypeEnum, MessageSendStatusEnum
from apps.base.utils.redis_util import RedisUtil
from apps.web.config.logger_config import logger
from apps.web.core.event.event_name import EventName
from apps.web.core.event.event_server import EventServer
from apps.web.dao.chat_dao import ChatDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.chat_dto import ChatMessageDTO, WSMessageDTO, SystemMessageDTO, UserProfileDTO, GroupProfileDTO, \
    GroupInfoDTO, ChangeCurrentConversationMessageDTO, ChatSaveMessageDTO, ChatSendMessageDTO, ConversationDTO, \
    FriendApplyMessageDTO
from apps.web.dto.notice_dto import NoticeSaveDTO
from apps.web.dto.user_dto import UserCommonInfoDTO, UserBaseInfoDTO

T = TypeVar("T", bound=BaseDTO)
MessageType: TypeAlias = NoticeSaveDTO | ChatSaveMessageDTO | SystemMessageDTO | ChangeCurrentConversationMessageDTO | FriendApplyMessageDTO


class ConnectManager:

    def __init__(self):
        self.user_websocket_dict: dict[int, WebSocket] = {}
        self.user_current_conversation_dict: dict[int, str] = {}
        self.group_conversation_user_dict: dict[str, set[int]] = {}
        self.user_info_dict: dict[int, UserProfileDTO] = {}
        self.group_info_dict: dict[int, GroupProfileDTO] = {}
        self.event_server = EventServer.get_instance()
        self.event_server.on(EventName.UPDATE_USER_INFO, self.update_user_info)
        self.event_server.on(EventName.UPDATE_GROUP_INFO, self.update_group_info)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        user_id = websocket.scope.get("user_id")
        if user_id in self.user_websocket_dict:
            await self.disconnect(self.user_websocket_dict[user_id])
        self.user_websocket_dict[user_id] = websocket

    async def disconnect(self, websocket: WebSocket):
        user_id = websocket.scope.get("user_id")
        self.user_websocket_dict.pop(user_id, None)
        self.user_current_conversation_dict.pop(user_id, None)
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close()
            except RuntimeError as e:
                pass

    async def broadcast(self, message: WSMessageDTO[ChatMessageDTO]):
        """
        群组消息
        :param message:
        :return:
        """
        chat_dao = GetBean(ChatDao)
        conversation_id = message.message.conversation_id
        if conversation_id not in self.group_conversation_user_dict:
            user_list = await chat_dao.get_group_members(message.message.contact_id)
            self.group_conversation_user_dict[conversation_id] = set(user_list)
        message.message.group_profile = self.group_info_dict.get(message.message.contact_id, GroupProfileDTO)
        tasks = []
        for user_id in self.group_conversation_user_dict[conversation_id]:
            websocket = self.user_websocket_dict.get(user_id)
            if websocket:
                message.message.is_read = self.check_group_message_read(user_id, message)
                if not message.message.is_read:
                    redis_util = GetBean(RedisUtil)
                    tasks.append(redis_util.Chat.incr_conversation_unread_count(user_id, conversation_id))
                message = jsonable_encoder(message)
                tasks.append(websocket.send_json(message))
        await asyncio.gather(*tasks)

    async def send_message(self, message: WSMessageDTO[MessageType]):
        """
        发送消息
        :param message:
        :return
        """
        try:
            if message.message_type == WSMessageTypeEnum.CHANGE_CURRENT_CONVERSATION:
                self.user_current_conversation_dict[message.message.user_id] = message.message.conversation_id
                return
            if message.message_type == WSMessageTypeEnum.SYSTEM_IN_TIME:
                await self.system_message(message)
                return
            if message.message_type == WSMessageTypeEnum.FRIEND_APPLY:
                message: WSMessageDTO[FriendApplyMessageDTO]
                send_other = self.user_websocket_dict.get(message.message.user_id)
                if send_other:
                    message = jsonable_encoder(message)
                    await send_other.send_json(message)
                return
            if message.message_type == WSMessageTypeEnum.NOTICE:
                message: WSMessageDTO[NoticeSaveDTO]
                send_other = self.user_websocket_dict.get(message.message.user_id)
                message = jsonable_encoder(message)
                await send_other.send_json(message)
                return
            if message.message_type == WSMessageTypeEnum.CHAT_MESSAGE:
                message: WSMessageDTO[ChatSendMessageDTO]
                redis_util = GetBean(RedisUtil)
                chat_dao = GetBean(ChatDao)
                temp_id = message.message.temp_id
                # 保存消息至数据库
                save_message = ChatSaveMessageDTO.model_validate(message.message, from_attributes=True)
                db_message = await chat_dao.save_message(save_message)
                # 封装消息
                message: WSMessageDTO[ChatMessageDTO] = WSMessageDTO[ChatMessageDTO](
                    message_type=WSMessageTypeEnum.CHAT_MESSAGE,
                    message=ChatMessageDTO.model_validate(db_message, from_attributes=True))
                message.message.temp_id = temp_id
                if message.message.contact_type == ContactTypeEnum.GROUP:
                    await self.broadcast(message)
                    return
                tasks = []
                # 检查对方用户是否停留在当前发送方会话
                message.message.is_read = self.check_message_read(message.message)
                if not message.message.is_read:
                    tasks.append(redis_util.Chat.incr_conversation_unread_count(message.message.contact_id,
                                                                                message.message.conversation_id))
                message.message.user_profile = await self.get_user_info(message.message.user_id, UserBaseInfoDTO)
                send_me = self.user_websocket_dict[message.message.user_id]
                send_other = self.user_websocket_dict.get(message.message.contact_id)
                message = jsonable_encoder(message)
                tasks.append(send_me.send_json(message))
                if send_other:
                    tasks.append(send_other.send_json(message))
                await asyncio.gather(*tasks)
        except Exception as e:
            await self._send_fail_message(message)
            logger.error(f"send_message error: {e}")

    async def _send_fail_message(self, message: WSMessageDTO[MessageType]):
        try:
            if message.message_type == WSMessageTypeEnum.CHAT_MESSAGE:
                message: WSMessageDTO[ChatSendMessageDTO]
                message.message.status = MessageSendStatusEnum.FAIL
                send_me = self.user_websocket_dict[message.message.user_id]
                message = jsonable_encoder(message)
                await send_me.send_json(message)
        except Exception as e:
            logger.error(f"send_fail_message error: ", exc_info=e)

    async def system_message(self, message: WSMessageDTO[SystemMessageDTO]):
        """
        系统及时消息，通知所有人
        :param message:
        :return:
        """
        message = jsonable_encoder(message)
        tasks = []
        for websocket in self.user_websocket_dict.values():
            tasks.append(websocket.send_json(message))
        await asyncio.gather(*tasks)

    async def get_user_info(self, user_id: int, clazz: Type[T] = UserCommonInfoDTO) -> T:
        if user_id not in self.user_info_dict:
            user_dao = GetBean(UserDao)
            user_info = await user_dao.get_user_info(user_id)
            self.user_info_dict[user_id] = user_info
        ret = self.user_info_dict[user_id]
        if clazz is UserCommonInfoDTO:
            return ret
        return clazz.model_validate(ret, from_attributes=True)

    async def update_user_info(self, user_id: int):
        user_dao = GetBean(UserDao)
        user_info = await user_dao.get_user_info(user_id)
        self.user_info_dict[user_id] = user_info

    async def get_group_info(self, group_id: int, clazz: Type[T] = GroupInfoDTO):
        if group_id not in self.group_info_dict:
            chat_dao = GetBean(ChatDao)
            group_info = await chat_dao.get_group_info(group_id)
            self.group_info_dict[group_id] = group_info
        ret = self.group_info_dict[group_id]
        if clazz is GroupInfoDTO:
            return ret
        return clazz.model_validate(ret, from_attributes=True)

    async def update_group_info(self, group_id: int):
        chat_dao = GetBean(ChatDao)
        group_info = await chat_dao.get_group_info(group_id)
        self.group_info_dict[group_id] = group_info

    def check_message_read(self, message: ChatMessageDTO):
        """
        检查对方是否停留在发送人聊天页面
        :param message:
        :return:
        """
        return self.user_current_conversation_dict.get(message.contact_id) == message.conversation_id

    def check_group_message_read(self, user_id: int, message: ChatMessageDTO):
        return self.user_current_conversation_dict.get(user_id) == message.conversation_id

    def is_online(self, conversation: ConversationDTO):
        if conversation.contact_type == ContactTypeEnum.GROUP:
            return True
        return conversation.contact_id in self.user_websocket_dict

    def gen_conversation_id(self, user_id: int, contact_id: int, contact_type: ContactTypeEnum):
        """
        生成会话id
        :param user_id:
        :param contact_id:
        :param contact_type:
        :return:
        """
        if contact_type == ContactTypeEnum.GROUP:
            return str(contact_id)
        return "".join(sorted([str(user_id), str(contact_id)]))


manager = ConnectManager()
