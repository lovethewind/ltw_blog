# @Time    : 2024/9/5 16:59
# @Author  : frank
# @File    : share_dto.py
from datetime import datetime
from typing import Any

from apps.base.enum.share import ShareTypeEnum
from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.user_dto import UserBaseInfoDTO


class ShareDTO(BaseDTO):
    id: int
    user_id: int
    content: str
    share_type: ShareTypeEnum
    tag: list[str]
    detail: list[dict[str, Any]]
    like_count: int = 0
    has_like: bool = False
    create_time: datetime
    update_time: datetime
    user: UserBaseInfoDTO = None
