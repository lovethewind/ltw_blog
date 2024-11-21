# @Time    : 2024/9/4 16:51
# @Author  : frank
# @File    : message_dto.py
from datetime import datetime
from typing import Optional

from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.user_dto import UserBaseInfoDTO


class MessageDTO(BaseDTO):
    id: int
    user_id: int
    nickname: Optional[str] = None
    parent_id: int
    reply_user_id: int
    first_level_id: int
    content: str
    avatar: Optional[str]
    address: str
    create_time: datetime
    children: list["MessageDTO"] = []
    children_count: int = 0
    user: Optional[UserBaseInfoDTO] = None
    reply_user: Optional[UserBaseInfoDTO] = None
