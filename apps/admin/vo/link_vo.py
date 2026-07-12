from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminLinkQueryVO(BaseVO):
    """
    后台友链查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    status: int | None = Field(default=None, ge=1, le=3)


class AdminLinkCreateVO(BaseVO):
    """
    后台友链创建参数。
    """

    name: str = Field(min_length=1, max_length=100)
    cover: str = Field(default="", max_length=300)
    introduce: str = Field(default="", max_length=1000)
    url: str = Field(min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=100)
    index: int = 100000
    status: int = Field(default=2, ge=1, le=3)
    description: str | None = Field(default=None, max_length=1000)


class AdminLinkUpdateVO(BaseVO):
    """
    后台友链更新参数。
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    cover: str | None = Field(default=None, max_length=300)
    introduce: str | None = Field(default=None, max_length=1000)
    url: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=100)
    index: int | None = None
    status: int | None = Field(default=None, ge=1, le=3)
    description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminLinkUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 友链更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self
