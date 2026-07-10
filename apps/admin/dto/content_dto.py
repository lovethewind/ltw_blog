from datetime import datetime

from pydantic import Field

from apps.admin.dto.base_dto import BaseDTO


class AdminCategoryDTO(BaseDTO):
    """
    后台分类 DTO。
    """

    id: int
    name: str
    description: str | None = None
    index: int
    is_active: bool


class AdminTagDTO(BaseDTO):
    """
    后台标签 DTO。
    """

    id: int
    parent_id: int
    name: str
    description: str | None = None
    level: int
    index: int
    is_active: bool
    children: list["AdminTagDTO"] = Field(default_factory=list)


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


AdminArticleDTO.model_rebuild()


class AdminCommentDTO(BaseDTO):
    """
    后台评论 DTO。
    """

    id: int
    user_id: int
    obj_id: int
    obj_type: int
    parent_id: int
    reply_user_id: int
    first_level_id: int
    content: str
    status: int
    create_time: datetime
    update_time: datetime


class AdminMessageDTO(BaseDTO):
    """
    后台留言 DTO。
    """

    id: int
    user_id: int
    avatar: str | None = None
    nickname: str | None = None
    email: str | None = None
    address: str
    content: str
    parent_id: int
    reply_user_id: int
    first_level_id: int
    create_time: datetime
    update_time: datetime


class AdminPictureAlbumDTO(BaseDTO):
    """
    后台图册 DTO。
    """

    id: int
    user_id: int
    name: str
    description: str | None = None
    cover: str
    status: int
    album_type: int
    create_time: datetime
    update_time: datetime


class AdminPictureDTO(BaseDTO):
    """
    后台图片 DTO。
    """

    id: int
    user_id: int
    album_id: int
    description: str | None = None
    url: str
    thumb_url: str = ""
    size: int
    width: int
    height: int
    status: int
    create_time: datetime
    update_time: datetime


class AdminLinkDTO(BaseDTO):
    """
    后台友链 DTO。
    """

    id: int
    name: str
    cover: str
    introduce: str
    url: str
    email: str | None = None
    index: int
    status: int
    description: str | None = None
    create_time: datetime
    update_time: datetime


class AdminWebsiteCategoryDTO(BaseDTO):
    """
    后台网站导航分类 DTO。
    """

    id: int
    name: str
    index: int
    create_time: datetime
    update_time: datetime


class AdminWebsiteDTO(BaseDTO):
    """
    后台网站导航 DTO。
    """

    id: int
    user_id: int
    name: str
    category_id: int
    cover: str
    introduce: str
    url: str
    index: int
    status: int
    create_time: datetime
    update_time: datetime


class AdminConfigDTO(BaseDTO):
    """
    后台配置 DTO。
    """

    id: int
    name: str
    value: str
    description: str | None = None
    is_active: bool
    create_time: datetime
    update_time: datetime
