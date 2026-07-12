from datetime import datetime

from pydantic import Field

from apps.admin.dto.base_dto import BaseDTO


class AdminArticleAuthorDTO(BaseDTO):
    """
    后台文章作者摘要 DTO。
    """

    id: int
    uid: int
    username: str
    nickname: str
    avatar: str | None = None
    email: str | None = None
    mobile: str | None = None
    gender: int
    address: str | None = None
    summary: str | None = None
    register_time: datetime
    last_login_time: datetime | None = None


class AdminArticleDTO(BaseDTO):
    """
    后台文章 DTO。
    """

    id: int
    user_id: int
    title: str
    cover: str
    cover_thumb: str = ""
    category_id: int
    tag_list: list[int] = Field(default_factory=list)
    attach_list: list[dict] = Field(default_factory=list)
    content: str
    is_markdown: bool
    is_original: bool
    original_url: str
    status: int
    is_deleted: bool
    edit_time: datetime | None = None
    create_time: datetime
    update_time: datetime
    author: AdminArticleAuthorDTO | None = None
