import datetime
from typing import Any, Self

from pydantic import BaseModel

from apps.base.utils.formatter_util import FormatterUtil


class BaseDTO(BaseModel):
    """
    自定义序列化响应字段
    """

    class Config:
        alias_generator = FormatterUtil.to_lower_camel
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            datetime.datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
            int: lambda x: str(x) if x and x > 2**31 else x,
        }

    @classmethod
    def bulk_model_validate(cls, objs: list[Any], **kwargs) -> list[Self]:
        """
        批量校验并转换模型对象。

        :param objs: 待转换的对象列表。
        :param kwargs: 透传给 Pydantic 的额外参数。
        :return: DTO 列表。
        """
        return [cls.model_validate(obj, from_attributes=True, **kwargs) for obj in objs]
