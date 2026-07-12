from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminConfigQueryVO(BaseVO):
    """
    后台配置查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class AdminConfigCreateVO(BaseVO):
    """
    后台配置创建参数。
    """

    name: str = Field(min_length=1, max_length=50)
    value: str
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = False


class AdminConfigUpdateVO(BaseVO):
    """
    后台配置更新参数。
    """

    name: str | None = Field(default=None, min_length=1, max_length=50)
    value: str | None = None
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminConfigUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 配置更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self
