from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminArticleQueryVO(BaseVO):
    """
    后台文章查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    category_id: int | None = None
    status: int | None = Field(default=None, ge=1, le=4)
    user_id: int | None = None
    is_original: bool | None = None


class AdminArticleCreateVO(BaseVO):
    """
    后台文章创建参数。
    """

    user_id: int
    title: str = Field(min_length=1, max_length=100)
    cover: str = Field(default="", max_length=512)
    cover_thumb: str = Field(default="", max_length=512)
    category_id: int
    tag_list: list[int] = Field(default_factory=list)
    attach_list: list[dict] = Field(default_factory=list)
    content: str = Field(min_length=1)
    is_markdown: bool = False
    is_original: bool = True
    original_url: str = Field(default="", max_length=512)
    status: int = Field(default=1, ge=1, le=4)


class AdminArticleUpdateVO(BaseVO):
    """
    后台文章更新参数。
    """

    user_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=100)
    cover: str | None = Field(default=None, max_length=512)
    cover_thumb: str | None = Field(default=None, max_length=512)
    category_id: int | None = None
    tag_list: list[int] | None = None
    attach_list: list[dict] | None = None
    content: str | None = None
    is_markdown: bool | None = None
    is_original: bool | None = None
    original_url: str | None = Field(default=None, max_length=512)
    status: int | None = Field(default=None, ge=1, le=4)

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminArticleUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 文章更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


class AdminArticleStatusVO(BaseVO):
    """
    后台文章状态更新参数。
    """

    status: int = Field(ge=1, le=4)
