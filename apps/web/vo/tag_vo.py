from pydantic import Field, field_validator

from apps.web.vo.base_vo import BaseVO


class TagCreateVO(BaseVO):
    """自定义标签创建参数。"""

    name: str = Field(min_length=1, max_length=20)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """
        规范化标签名称并拒绝纯空白内容。

        :param value: 原始标签名称。
        :return: 合并多余空白后的标签名称。
        :raises ValueError: 标签名称为空时抛出。
        """
        normalized_name = " ".join(value.split())
        if not normalized_name:
            raise ValueError("标签名称不能为空")
        return normalized_name
