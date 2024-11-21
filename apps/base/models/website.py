from tortoise import fields

from apps.base.enum.common import CheckStatusEnum
from apps.base.models.base import BaseModel


class Website(BaseModel):
    user_id = fields.BigIntField(description="用户id")
    name = fields.CharField(max_length=100, description="网站名")
    category_id = fields.BigIntField(description="分类id")
    cover = fields.CharField(max_length=300, description="封面")
    introduce = fields.CharField(max_length=1000, description="简介")
    url = fields.CharField(max_length=100, description="url")
    index = fields.IntField(default=100000, description="排序")
    status = fields.IntEnumField(CheckStatusEnum, defalut=CheckStatusEnum.PASS,
                                 description="审核状态: 1: 已通过 2:审核中 3:拒绝")

    class Meta:
        table = "t_website"
        table_description = "网站导航表"


class WebsiteCategory(BaseModel):
    name = fields.CharField(max_length=100, description="分类名")
    index = fields.IntField(default=100000, description="排序")

    class Meta:
        table = "t_website_category"
        table_description = "网站导航分类表"
