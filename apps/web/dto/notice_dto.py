# @Time    : 2024/10/21 18:00
# @Author  : frank
# @File    : notice_dto.py
from datetime import datetime
from typing import Optional, Any

from apps.base.enum.action import ObjectTypeEnum
from apps.base.enum.notice import NoticeTypeEnum
from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.user_dto import UserSimpleInfoDTO


class NoticeDetailDTO(BaseDTO):
    from_user_id: Optional[int] = None
    from_user: Optional[UserSimpleInfoDTO] = None
    obj_id: Optional[int] = None
    obj_content: Optional[str] = None  # 文章为标题，图片为url，分享为内容
    obj_type: Optional[ObjectTypeEnum] = None
    comment_type: Optional[ObjectTypeEnum] = None  # 评论主题类型(点赞评论使用)
    comment_id: Optional[int] = None  # 回复的评论id
    comment_content: Optional[str] = None  # 回复的评论内容


class NoticeDTO(BaseDTO):
    id: int
    title: str
    content: str
    detail: NoticeDetailDTO
    notice_type: NoticeTypeEnum
    is_read: bool
    create_time: datetime


class NoticeSaveDTO(BaseDTO):
    user_id: int = 0
    title: str = ""
    content: str = ""
    detail: NoticeDetailDTO
    notice_type: NoticeTypeEnum = NoticeTypeEnum.SYSTEM
    is_read: bool = False

    def __init__(self, /, **data: Any):
        if "detail" not in data:
            data["detail"] = NoticeDetailDTO()
        super().__init__(**data)
