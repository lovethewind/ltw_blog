from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


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
