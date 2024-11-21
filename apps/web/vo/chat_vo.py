# @Time    : 2024/11/4 15:54
# @Author  : frank
# @File    : chat_vo.py
from typing import Optional

from fastapi import Query

from apps.base.enum.chat import ContactTypeEnum, ContactApplyStatusEnum
from apps.web.vo.base_vo import BaseVO


class ConversationVO(BaseVO):
    contact_id: int = Query()
    contact_type: ContactTypeEnum = Query()


class HistoryMessageVO(BaseVO):
    conversation_id: str = Query()
    next_message_id: Optional[int] = Query(default=None)


class ConversationUpdateVO(BaseVO):
    conversation_id: Optional[str] = None
    is_muted: Optional[bool] = None
    is_pinned: Optional[bool] = None
    is_clear: Optional[bool] = None
    all_read: Optional[bool] = None


class ContactVO(BaseVO):
    contact_id: int


class ContactApplyVO(BaseVO):
    contact_id: int
    contact_type: ContactTypeEnum
    content: str


class HandleContactApplyVO(BaseVO):
    contact_id: int
    status: ContactApplyStatusEnum
