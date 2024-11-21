# @Time    : 2024/10/21 16:05
# @Author  : frank
# @File    : notice.py
from tortoise import fields

from apps.base.enum.notice import NoticeTypeEnum
from apps.base.models.base import BaseModel


class Notice(BaseModel):
    """
    通知消息
    """
    user_id = fields.BigIntField(description="用户id")
    title = fields.CharField(max_length=255, description="标题")
    content = fields.TextField(description="内容", default="")
    notice_type = fields.IntEnumField(NoticeTypeEnum, default=NoticeTypeEnum.SYSTEM, description="消息类型")
    is_read = fields.BooleanField(default=False, description="是否已读")
    detail = fields.JSONField(description="详情", default={})

    class Meta:
        table = "t_notice"
        table_description = "通知消息表"
