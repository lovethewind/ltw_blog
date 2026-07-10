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


class AdminCommentQueryVO(BaseVO):
    """
    后台评论查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    obj_id: int | None = None
    obj_type: int | None = Field(default=None, ge=1, le=5)
    status: int | None = Field(default=None, ge=1, le=3)
    user_id: int | None = None


class AdminCommentUpdateVO(BaseVO):
    """
    后台评论更新参数。
    """

    content: str | None = None
    status: int | None = Field(default=None, ge=1, le=3)

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminCommentUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 评论更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


class AdminCommentStatusVO(BaseVO):
    """
    后台评论状态更新参数。
    """

    status: int = Field(ge=1, le=3)


class AdminMessageQueryVO(BaseVO):
    """
    后台留言查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    user_id: int | None = None
    parent_id: int | None = None


class AdminMessageUpdateVO(BaseVO):
    """
    后台留言更新参数。
    """

    nickname: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=100)
    content: str | None = None
    avatar: str | None = Field(default=None, max_length=300)
    address: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminMessageUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 留言更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


class AdminCategoryCreateVO(BaseVO):
    """
    后台分类创建参数。
    """

    name: str = Field(min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=1000)
    index: int = 100000
    is_active: bool = True


class AdminCategoryUpdateVO(BaseVO):
    """
    后台分类更新参数。
    """

    name: str | None = Field(default=None, min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=1000)
    index: int | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminCategoryUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 分类更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


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


class AdminCheckStatusVO(BaseVO):
    """
    后台审核状态更新参数。
    """

    status: int = Field(ge=1, le=3)


class AdminPictureAlbumQueryVO(BaseVO):
    """
    后台图册查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    status: int | None = Field(default=None, ge=1, le=3)
    album_type: int | None = Field(default=None, ge=1, le=2)
    user_id: int | None = None


class AdminPictureAlbumCreateVO(BaseVO):
    """
    后台图册创建参数。
    """

    user_id: int
    name: str = Field(min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=200)
    cover: str = Field(min_length=1, max_length=512)
    status: int = Field(default=1, ge=1, le=3)
    album_type: int = Field(default=2, ge=1, le=2)


class AdminPictureAlbumUpdateVO(BaseVO):
    """
    后台图册更新参数。
    """

    user_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=200)
    cover: str | None = Field(default=None, min_length=1, max_length=512)
    status: int | None = Field(default=None, ge=1, le=3)
    album_type: int | None = Field(default=None, ge=1, le=2)

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminPictureAlbumUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 图册更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


class AdminPictureQueryVO(BaseVO):
    """
    后台图片查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    album_id: int | None = None
    status: int | None = Field(default=None, ge=1, le=3)
    user_id: int | None = None


class AdminPictureCreateVO(BaseVO):
    """
    后台图片创建参数。
    """

    user_id: int
    album_id: int
    description: str | None = Field(default=None, max_length=200)
    url: str = Field(min_length=1, max_length=512)
    thumb_url: str = Field(default="", max_length=512)
    size: int = Field(default=0, ge=0)
    width: int = Field(default=0, ge=0)
    height: int = Field(default=0, ge=0)
    status: int = Field(default=1, ge=1, le=3)


class AdminPictureUpdateVO(BaseVO):
    """
    后台图片更新参数。
    """

    user_id: int | None = None
    album_id: int | None = None
    description: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, min_length=1, max_length=512)
    thumb_url: str | None = Field(default=None, max_length=512)
    size: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=0)
    height: int | None = Field(default=None, ge=0)
    status: int | None = Field(default=None, ge=1, le=3)

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminPictureUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 图片更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


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


class AdminWebsiteCategoryCreateVO(BaseVO):
    """
    后台网站导航分类创建参数。
    """

    name: str = Field(min_length=1, max_length=100)
    index: int = 100000


class AdminWebsiteCategoryUpdateVO(BaseVO):
    """
    后台网站导航分类更新参数。
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    index: int | None = None

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminWebsiteCategoryUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 网站导航分类更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


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
