from email.policy import default
from enum import IntEnum
from typing import Optional

from pydantic import Field

from apps.base.utils.ip_util import IpUtil
from apps.web.core.context_vars import ContextVars
from apps.web.vo.base_vo import BaseVO


class LoginVO(BaseVO):
    username: Optional[str] = Field(default=None, min_length=3, max_length=20)
    email: Optional[str] = Field(default=None, max_length=50,
                                 pattern=r"^[A-Za-z0-9+_.-]+[a-zA-Z0-9_-]@[A-Za-z0-9_-]+(\.[A-Za-z]+)+$")
    mobile: Optional[str] = Field(default=None, pattern=r"^1[345789][0-9]{9}$")
    password: Optional[str] = Field(default=None)
    code: Optional[str] = Field(default=None, min_length=6, max_length=6)


class RegisterVO(BaseVO):
    nickname: str = Field(min_length=1, max_length=20)
    username: str = Field(min_length=3, max_length=20)
    email: str = Field(default=None, pattern=r"^[A-Za-z0-9+_.-]+[a-zA-Z0-9_-]@[A-Za-z0-9_-]+(\.[A-Za-z]+)+$")
    mobile: str = Field(default=None, pattern=r"^1[345789][0-9]{9}$")
    password: str = Field(pattern=r"^[a-zA-Z\d\W]{6,30}$")
    code: str = Field(min_length=6, max_length=20)

    def biz_key(self) -> str:
        return f"user_register:{self.email}_{self.mobile}_{self.code}"


class ForgetPasswordVO(BaseVO):
    email: Optional[str] = Field(default=None, pattern=r"^[A-Za-z0-9+_.-]+[a-zA-Z0-9_-]@[A-Za-z0-9_-]+(\.[A-Za-z]+)+$")
    mobile: Optional[str] = Field(default=None, pattern=r"^1[345789][0-9]{9}$")
    password: str = Field(pattern=r"^[a-zA-Z\d\W]{6,30}$")
    code: str = Field(min_length=6, max_length=6)


class ChangePasswordTypeEnum(IntEnum):
    # 修改密码方式 1. 原密码 2.邮箱验证码 3.手机验证码 4.微信扫码
    OLD_PASSWORD = 1
    EMAIL_CODE = 2
    MOBILE_CODE = 3
    WECHAT_SCAN = 4


class ChangePasswordVO(BaseVO):
    change_type: ChangePasswordTypeEnum
    code: Optional[str] = Field(default=None, min_length=6, max_length=6)
    random_code: Optional[str] = Field(default=None, min_length=6, max_length=6)
    old_password: Optional[str] = Field(default=None, min_length=1, max_length=30)
    password: str = Field(min_length=6, max_length=30)


class UserUpdateVO(BaseVO):
    nickname: Optional[str] = Field(default=None, max_length=20)
    gender: Optional[int] = Field(default=None)
    avatar: Optional[str] = Field(default=None)
    occupation: Optional[str] = Field(default=None, max_length=20)
    summary: Optional[str] = Field(default=None, max_length=100)
    background: Optional[str] = Field(default=None)


class ChangeEmailBindVO(BaseVO):
    email: str = Field(default=None, pattern=r"^[A-Za-z0-9+_.-]+[a-zA-Z0-9_-]@[A-Za-z0-9_-]+(\.[A-Za-z]+)+$")
    old_code: str = Field(default=None, min_length=6, max_length=6)
    code: str = Field(min_length=6, max_length=6)

    def biz_key(self) -> str | None:
        return f"change_email_bind:{self.email}"


class ChangeMobileBindVO(BaseVO):
    mobile: str = Field(default=None, pattern=r"^1[345789][0-9]{9}$")
    old_code: str = Field(default=None, min_length=6, max_length=6)
    code: str = Field(min_length=6, max_length=6)

    def biz_key(self) -> str | None:
        return f"change_mobile_bind:{self.mobile}"


class WechatBindParamsVO(BaseVO):
    code: str
    old_code: Optional[str]


class ValidateAccountExistVO(BaseVO):
    username: str = None
    email: str = None
    mobile: str = None


class AddUserViewCountVO(BaseVO):
    user_id: int

    @property
    def biz_key(self) -> str | None:
        request = ContextVars.request.get()
        ip_address = IpUtil.get_ip_address(request)
        return f"add_user_view_count:{self.user_id}:{ip_address}"
