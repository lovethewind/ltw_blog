from tortoise import fields

from apps.base.enum.common import CheckStatusEnum
from apps.base.enum.share import ShareTypeEnum
from apps.base.models.base import BaseModel


class Share(BaseModel):
    user_id = fields.BigIntField(description="用户id")
    content = fields.TextField(description="内容")
    share_type = fields.IntEnumField(ShareTypeEnum, defalut=ShareTypeEnum.NOTE,
                                     description="分享类型 1：笔记 2：生活 3：经验 4：音乐 5：视频 6：资源 7：其他")
    tag = fields.JSONField(default=[], description="标签")
    detail = fields.JSONField(default=[], description="详情")
    status = fields.IntEnumField(CheckStatusEnum, description="状态 1:通过 2:审核中 3:拒绝",
                                 default=CheckStatusEnum.PASS)

    class Meta:
        table = "t_share"
        table_description = "分享表"
