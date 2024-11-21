from tortoise import fields

from apps.base.enum.common import CheckStatusEnum
from apps.base.models.base import BaseModel


class Link(BaseModel):
    name = fields.CharField(max_length=100, description="网站名")
    cover = fields.CharField(max_length=300, description="封面")
    introduce = fields.CharField(max_length=1000, description="简介")
    url = fields.CharField(max_length=100, description="url")
    email = fields.CharField(max_length=100, null=True, description="联系人邮箱")
    index = fields.IntField(default=100000, description="排序")
    status = fields.IntEnumField(CheckStatusEnum, defalut=CheckStatusEnum.CHECKING,
                                 description="审核状态: 1: 已通过 2:审核中 3:拒绝")
    description = fields.CharField(max_length=1000, default='', description="说明")

    class Meta:
        table = "t_link"
        table_description = "友链表"
