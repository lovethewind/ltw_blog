# @Time    : 2024/8/28 14:43
# @Author  : frank
# @File    : comment_dto.py
from datetime import datetime

from apps.base.enum.action import ObjectTypeEnum
from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.user_dto import UserBaseInfoDTO


class CommentDTO(BaseDTO):
    id: int
    user_id: int
    obj_id: int
    obj_type: ObjectTypeEnum
    parent_id: int
    reply_user_id: int
    first_level_id: int
    status: int
    content: str
    create_time: datetime
    has_like: bool = False
    like_count: int = 0
    children: list["CommentDTO"] = []
    children_count: int = 0
    user: UserBaseInfoDTO = None
    reply_user: UserBaseInfoDTO = None
