import datetime
from typing import Type, Any, Self

from pydantic import BaseModel

from apps.base.utils.formatter_util import FormatterUtil


class BaseDTO(BaseModel):
    """
    自定义序列化响应字段
    """

    class Config:
        alias_generator = FormatterUtil.to_lower_camel
        populate_by_name = True
        json_encoders = {
            datetime.datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
            int: lambda x: str(x) if x and x > 2 ** 31 else x
        }

    @classmethod
    def model_validate[T](cls: Type[T],
                       obj: Any,
                       nullable: bool = True,
                       *,
                       strict: bool | None = None,
                       from_attributes: bool | None = None,
                       context: dict[str, Any] | None = None) -> T | None:
        """
        重写model_validate方法，使用该方法时，如果对象为空，且nullable为True时则返回None替代抛异常
        """
        if not obj and nullable:
            return
        return super().model_validate(obj, strict=strict, from_attributes=from_attributes, context=context)

    @classmethod
    def bulk_model_validate(cls, objs: list[Any], **kwargs) -> list[Self]:
        return [cls.model_validate(obj, from_attributes=True, **kwargs) for obj in objs]
