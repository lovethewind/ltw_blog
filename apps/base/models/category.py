from tortoise import fields

from apps.base.constant.common_constant import CommonConstant
from apps.base.enum.category import TagLevelEnum
from apps.base.models.base import BaseModel


class Category(BaseModel):
    name = fields.CharField(max_length=20, description="分类名")
    description = fields.CharField(max_length=1000, null=True, description="描述")
    index = fields.IntField(default=100000, description="排序(越小越在前)")
    is_active = fields.BooleanField(default=True, description="是否激活")

    class Meta:
        table = "t_category"
        table_description = "分类表"


class Tag(BaseModel):
    name = fields.CharField(max_length=20, description="标签名")
    description = fields.CharField(max_length=1000, null=True, description="描述")
    parent_id = fields.BigIntField(default=CommonConstant.TOP_LEVEL, description="所属父级")
    level = fields.IntEnumField(TagLevelEnum, default=TagLevelEnum.CATEGORY, description="层级(1:分类层 2:展示层)")
    index = fields.IntField(default=100000, description="排序(越小越在前)")
    is_active = fields.BooleanField(default=True, description="是否激活")

    class Meta:
        table = "t_tag"
        table_description = "标签表"
