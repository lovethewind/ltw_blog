from tortoise import fields
from tortoise.models import Model, ModelMeta

from apps.base.utils.snowflake import SnowflakeIDGenerator


class BaseModelMeta(ModelMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        meta = namespace.get('Meta', None)
        if meta:
            meta.ordering = ['-id']
        cls = super().__new__(mcs, name, bases, namespace)
        return cls


class BaseModel(Model, metaclass=BaseModelMeta):
    id = fields.BigIntField(pk=True, generated=False, default=SnowflakeIDGenerator.generate_id, description="主键")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        abstract = True

    def model_dump(self):
        return {item: getattr(self, item) for item in self._meta.fields}
