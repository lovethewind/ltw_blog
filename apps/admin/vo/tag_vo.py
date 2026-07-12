from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminTagCreateVO(BaseVO):
    """
    后台标签创建参数。
    """

    parent_id: int = 0
    name: str = Field(min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=1000)
    level: int = Field(default=1, ge=1, le=2)
    index: int = 100000
    is_active: bool = True


class AdminTagUpdateVO(BaseVO):
    """
    后台标签更新参数。
    """

    parent_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=1000)
    level: int | None = Field(default=None, ge=1, le=2)
    index: int | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminTagUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 标签更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self
