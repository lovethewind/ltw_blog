from datetime import datetime

from pydantic import Field

from apps.admin.dto.base_dto import BaseDTO


class AdminUserInfoDTO(BaseDTO):
    """
    后台管理员信息 DTO。
    """

    id: int
    uid: int
    username: str
    nickname: str
    avatar: str | None = None
    email: str | None = None
    mobile: str | None = None
    home_path: str | None = None
    real_name: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class AdminUserDTO(BaseDTO):
    """
    后台用户管理 DTO。
    """

    id: int
    uid: int
    username: str
    nickname: str
    gender: int
    avatar: str | None = None
    email: str | None = None
    mobile: str | None = None
    wechat: str | None = None
    register_time: datetime
    last_login_time: datetime | None = None
    last_login_ip: str | None = None
    summary: str | None = None
    address: str | None = None
    is_official: bool
    role_ids: list[int] = Field(default_factory=list)
