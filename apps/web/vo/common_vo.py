# @Time    : 2024/10/17 17:38
# @Author  : frank
# @File    : common_vo.py
from typing import Optional

from pydantic import Field

from apps.base.enum.common import FeedbackTypeEnum, VerifyCodeTypeEnum
from apps.web.vo.base_vo import BaseVO


class EmailCodeVO(BaseVO):
    email: str = Field(default=None, pattern=r"^[A-Za-z0-9+_.-]+[a-zA-Z0-9_-]@[A-Za-z0-9_-]+(\.[A-Za-z]+)+$")
    code: Optional[str] = Field(default=None, min_length=6, max_length=6)
    code_type: VerifyCodeTypeEnum


class UserEmailCodeVO(BaseVO):
    code: Optional[str] = Field(default=None, min_length=6, max_length=6)
    code_type: VerifyCodeTypeEnum


class MobileCodeVO(BaseVO):
    mobile: str = Field(default=None, pattern=r"^1[345789][0-9]{9}$")
    code: Optional[str] = Field(default=None, min_length=6, max_length=6)
    code_type: VerifyCodeTypeEnum

    def biz_key(self) -> str | None:
        return f"user_mobile_code:{self.mobile}"


class UserMobileCodeVO(BaseVO):
    code: Optional[str] = Field(default=None, min_length=6, max_length=6)
    code_type: VerifyCodeTypeEnum

    def biz_key(self) -> str | None:
        return f"user_mobile_code:{self.mobile}"


class FeedbackVO(BaseVO):
    feedback_type: FeedbackTypeEnum

    email: str

    title: str

    content: str
