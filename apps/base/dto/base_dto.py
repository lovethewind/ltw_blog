import datetime
from typing import Any, Self

from pydantic import BaseModel

from apps.base.utils.formatter_util import FormatterUtil


class BaseDTO(BaseModel):
    """
    通用 DTO 基类，提供统一字段别名和 JSON 序列化规则。
    """

    class Config:
        alias_generator = FormatterUtil.to_lower_camel
        populate_by_name = True
        json_encoders = {
            datetime.datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
            int: lambda x: str(x) if x and x > 2**31 else x,
        }

    @classmethod
    def bulk_model_validate(cls, objs: list[Any], **kwargs: Any) -> list[Self]:
        """
        批量转换对象为当前 DTO。

        :param objs: 待转换对象列表。
        :param kwargs: 传递给 Pydantic model_validate 的额外参数。
        :return: 当前 DTO 实例列表。
        """
        return [cls.model_validate(obj, from_attributes=True, **kwargs) for obj in objs]
