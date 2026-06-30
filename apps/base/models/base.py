from tortoise import fields, Model
from tortoise.manager import Manager
from tortoise.models import Model, ModelMeta
from tortoise.queryset import QuerySet
from typing_extensions import Self

from apps.base.utils.snowflake import SnowflakeIDGenerator


class BaseQuerySet[T](QuerySet[T]):
    """
    项目通用查询集。
    """

    def page(self, current: int, size: int) -> QuerySet[Model]:
        """
        拼接分页偏移和分页大小。

        :param current: 当前页码。
        :param size: 每页数量。
        :return: 拼接 offset 和 limit 后的查询集。
        """
        current = current if current > 0 else 1
        size = size if size > 0 else 10
        return self.offset((current - 1) * size).limit(size)


class BaseManager(Manager):
    """
    项目通用模型管理器。
    """

    def get_queryset(self) -> BaseQuerySet:
        """
        获取项目通用查询集。

        :return: 项目通用查询集。
        """
        return BaseQuerySet(self._model)


class BaseModelMeta(ModelMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        meta = namespace.get("Meta")
        if meta is None:
            meta = type("Meta", (), {})
            namespace["Meta"] = meta
        meta.ordering = ["-id"]
        if not hasattr(meta, "manager"):
            meta.manager = BaseManager()
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
