from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminUserQueryVO(BaseVO):
    """
    后台用户查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=500)
    keyword: str | None = Field(default=None, max_length=50)


class AdminUserCreateVO(BaseVO):
    """
    后台用户创建参数。
    """

    username: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=1, max_length=128)
    nickname: str = Field(min_length=1, max_length=20)
    gender: int = Field(default=0, ge=0, le=2)
    avatar: str = Field(default="", max_length=512)
    email: str | None = Field(default=None, max_length=128)
    mobile: str | None = Field(default=None, max_length=20)
    wechat: str | None = Field(default=None, max_length=128)
    summary: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=100)
    is_official: bool = False
    role_ids: list[int] = Field(default_factory=list)


class AdminUserUpdateVO(BaseVO):
    """
    后台用户更新参数。
    """

    username: str | None = Field(default=None, min_length=1, max_length=20)
    password: str | None = Field(default=None, min_length=1, max_length=128)
    nickname: str | None = Field(default=None, min_length=1, max_length=20)
    gender: int | None = Field(default=None, ge=0, le=2)
    avatar: str | None = Field(default=None, max_length=512)
    email: str | None = Field(default=None, max_length=128)
    mobile: str | None = Field(default=None, max_length=20)
    wechat: str | None = Field(default=None, max_length=128)
    summary: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=100)
    is_official: bool | None = None
    role_ids: list[int] | None = None

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminUserUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 用户更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


class AdminUserRoleUpdateVO(BaseVO):
    """
    后台用户角色更新参数。
    """

    role_ids: list[int] = Field(default_factory=list)
