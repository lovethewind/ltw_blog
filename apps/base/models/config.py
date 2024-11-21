from tortoise import fields

from apps.base.models.base import BaseModel


class Config(BaseModel):
    name = fields.CharField(max_length=50, description="配置key")
    value = fields.TextField(description="配置value")
    description = fields.CharField(max_length=1000, default='', description="配置说明")
    is_active = fields.BooleanField(default=False, description="是否启用")

    class Meta:
        table = "t_config"
        table_description = "配置表"
