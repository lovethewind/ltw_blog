# @Time    : 2024/8/13 22:45
# @Author  : frank
# @File    : base_vo.py
import inspect
from dataclasses import dataclass
from typing import Any, Type

from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass

from apps.base.utils.formatter_util import FormatterUtil


class BaseVOMetaclass(ModelMetaclass):
    def __new__(mcs, cls_name: str, bases: tuple[type], namespace: dict[str, Any], *args, **kwargs):
        cls = super().__new__(mcs, cls_name, bases, namespace, *args, **kwargs)
        config = getattr(cls, "Config", None)
        data_to_model = getattr(config, "data_to_model", None)
        if data_to_model:
            namespace.update(getattr(cls, "model_fields"))  # 更新别名等
            proxy_cls = mcs._generate_proxy_cls(cls_name, namespace)
            # 替换cls的签名
            cls.__signature__ = inspect.signature(proxy_cls)
        return cls

    @staticmethod
    def _generate_proxy_cls(cls_name: str, namespace: dict[str, Any]):
        cls = type[Type](f"{cls_name}Proxy", (), namespace)
        return dataclass(cls)


class BaseVO(BaseModel, metaclass=BaseVOMetaclass):
    class Config:
        alias_generator = FormatterUtil.to_lower_camel
        populate_by_name = True

    @property
    def biz_key(self) -> str | None:
        """
        业务key
        :return:
        """
        return
