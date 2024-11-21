# @Time    : 2024/11/4 14:39
# @Author  : frank
# @File    : chat_dto.py
import json
from datetime import datetime
from typing import Optional, Any

from apps.base.enum.chat import ContactTypeEnum, ChatMessageTypeEnum, WSMessageTypeEnum, WSMessageShowType, \
    ChatGroupTypeEnum, MessageSendStatusEnum, ContactApplyStatusEnum
from apps.web.dto.base_dto import BaseDTO


class UserProfileDTO(BaseDTO):
    id: int
    avatar: str
    nickname: str


class GroupProfileDTO(BaseDTO):
    id: int
    avatar: str
    name: str
    group_type: ChatGroupTypeEnum


class GroupInfoDTO(BaseDTO):
    id: int
    avatar: str
    name: str
    description: str
    notice: str
    group_type: ChatGroupTypeEnum


class AttachDTO(BaseDTO):
    url: str
    name: str
    size: int
    type: str


class ChatSaveMessageDTO(BaseDTO):
    user_id: int
    contact_id: int
    contact_type: ContactTypeEnum
    conversation_id: str
    message_type: ChatMessageTypeEnum
    content: str
    attach: Optional[list[AttachDTO]] = []


class ChatSendMessageDTO(BaseDTO):
    user_id: int = None
    contact_id: int
    contact_type: ContactTypeEnum
    conversation_id: str
    message_type: ChatMessageTypeEnum
    content: str
    attach: Optional[list[AttachDTO]] = []
    temp_id: str
    status: MessageSendStatusEnum


class ChatMessageDTO(BaseDTO):
    id: int
    user_id: int
    contact_id: int
    contact_type: ContactTypeEnum
    conversation_id: str
    user_profile: Optional[UserProfileDTO] = None
    group_profile: Optional[GroupProfileDTO] = None
    message_type: ChatMessageTypeEnum
    content: str
    attach: list[AttachDTO] = None
    is_read: bool = False
    create_time: datetime = None
    temp_id: str = None
    status: MessageSendStatusEnum = MessageSendStatusEnum.SUCCESS

    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs):
        if isinstance(obj, dict):
            obj["attach"] = json.loads(obj.get("attach", "[]"))
        return super().model_validate(obj, *args, **kwargs)


class ChatMessageResultDTO(BaseDTO):
    records: list[ChatMessageDTO]
    next_message_id: Optional[int] = None
    no_more: bool = True


class WSMessageDTO[T](BaseDTO):
    """
    websocket顶部类
    """
    message_type: WSMessageTypeEnum = WSMessageTypeEnum.NOTICE
    show_type: WSMessageShowType = WSMessageShowType.NOTIFICATION
    message: T


class SystemMessageDTO(BaseDTO):
    title: str
    content: str


class ChangeCurrentConversationMessageDTO(BaseDTO):
    user_id: int = None
    conversation_id: str


class FriendApplyMessageDTO(BaseDTO):
    user_id: int
    status: ContactApplyStatusEnum = ContactApplyStatusEnum.PENDING
    user_profile: Optional[UserProfileDTO] = None


###################


class ConversationDTO(BaseDTO):
    contact_id: int
    contact_type: ContactTypeEnum
    conversation_id: str
    is_muted: bool
    is_pinned: bool
    unread_count: int
    user_profile: Optional[UserProfileDTO] = None
    group_profile: Optional[GroupProfileDTO] = None
    last_message: Optional[ChatMessageDTO] = None
    online: bool = False
    last_clear_time: Optional[datetime] = None


class ContactApplyDTO(BaseDTO):
    id: int
    user_id: int
    contact_id: int
    contact_type: ContactTypeEnum
    content: str
    status: ContactApplyStatusEnum
    create_time: datetime
    update_time: datetime
    user_profile: UserProfileDTO = None


class ContactDTO(BaseDTO):
    contact_id: int
    contact_type: ContactTypeEnum
    user_profile: Optional[UserProfileDTO] = None
    group_profile: Optional[GroupProfileDTO] = None
    create_time: datetime
