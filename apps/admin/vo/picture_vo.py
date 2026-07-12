from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


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
