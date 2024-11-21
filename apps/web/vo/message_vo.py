# @Time    : 2024/9/4 17:26
# @Author  : frank
# @File    : message_vo.py
from typing import Optional

from apps.base.constant.common_constant import CommonConstant
from apps.web.vo.base_vo import BaseVO


class MessageAddVO(BaseVO):
    nickname: Optional[str] = None
    email: Optional[str] = None
    content: str
    avatar: Optional[str] = None
    parent_id: Optional[int] = CommonConstant.TOP_LEVEL
    reply_user_id: Optional[int] = CommonConstant.TOP_LEVEL
    first_level_id: Optional[int] = CommonConstant.TOP_LEVEL
