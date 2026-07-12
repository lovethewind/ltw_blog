from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminWebsiteQueryVO(BaseVO):
    """
    后台网站导航查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    category_id: int | None = None
    status: int | None = Field(default=None, ge=1, le=3)
    user_id: int | None = None


class AdminWebsiteCreateVO(BaseVO):
    """
    后台网站导航创建参数。
    """

    user_id: int
    name: str = Field(min_length=1, max_length=100)
    category_id: int
    cover: str = Field(default="", max_length=300)
    introduce: str = Field(default="", max_length=1000)
    url: str = Field(min_length=1, max_length=100)
    index: int = 100000
    status: int = Field(default=1, ge=1, le=3)


class AdminWebsiteUpdateVO(BaseVO):
    """
    后台网站导航更新参数。
    """

    user_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category_id: int | None = None
    cover: str | None = Field(default=None, max_length=300)
    introduce: str | None = Field(default=None, max_length=1000)
    url: str | None = Field(default=None, min_length=1, max_length=100)
    index: int | None = None
    status: int | None = Field(default=None, ge=1, le=3)

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminWebsiteUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 网站导航更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self
