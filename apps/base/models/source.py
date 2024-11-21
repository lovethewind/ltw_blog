from tortoise import fields

from apps.base.models.base import BaseModel


class Source(BaseModel):
    """
    定期删除已不再使用的资源
    """
    user_id = fields.BigIntField(description="用户id")
    url = fields.CharField(max_length=256, description="url")
    is_deleted = fields.BooleanField(default=False, description="是否已删除(实现逻辑删除)")

    class Meta:
        table = "t_source"
        table_description = "资源表"
