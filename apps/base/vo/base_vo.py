import inspect
from dataclasses import dataclass
from typing import Any, Type

from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass

from apps.base.utils.formatter_util import FormatterUtil


class BaseVOMetaclass(ModelMetaclass):
    """
    通用 VO 元类，支持按配置生成 dataclass 形式的签名。
    """

    def __new__(
        mcs, cls_name: str, bases: tuple[type, ...], namespace: dict[str, Any], *args: Any, **kwargs: Any
    ) -> type:
        """
        创建 VO 类型并按需替换构造签名。

        :param cls_name: 类名。
        :param bases: 父类列表。
        :param namespace: 类命名空间。
        :param args: 额外位置参数。
        :param kwargs: 额外关键字参数。
        :return: 创建后的 VO 类。
        """
        cls = super().__new__(mcs, cls_name, bases, namespace, *args, **kwargs)
        config = getattr(cls, "Config", None)
        data_to_model = getattr(config, "data_to_model", None)
        if data_to_model:
            namespace.update(getattr(cls, "model_fields"))
            proxy_cls = mcs._generate_proxy_cls(cls_name, namespace)
            cls.__signature__ = inspect.signature(proxy_cls)
        return cls

    @staticmethod
    def _generate_proxy_cls(cls_name: str, namespace: dict[str, Any]) -> type:
        """
        生成用于推导构造签名的代理类。

        :param cls_name: 原始类名。
        :param namespace: 类命名空间。
        :return: 代理类。
        """
        cls = type[Type](f"{cls_name}Proxy", (), namespace)
        return dataclass(cls)


class BaseVO(BaseModel, metaclass=BaseVOMetaclass):
    """
    通用请求 VO 基类。
    """

    class Config:
        alias_generator = FormatterUtil.to_lower_camel
        populate_by_name = True

    @property
    def biz_key(self) -> str | None:
        """
        获取防重复提交业务键。

        :return: 业务键，默认返回 None。
        """
        return None
