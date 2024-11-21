from enum import IntEnum
from typing import Optional, TypeAlias

from pydantic import Field

from apps.base.enum.user import GenderEnum, UserSettingsEnum
from apps.web.dto.base_dto import BaseDTO

UserSettingsType: TypeAlias = dict[UserSettingsEnum, str | bool]

class UserRestrictionDTO(BaseDTO):
    user_forbidden: bool = False
    comment_forbidden: bool = False


class UserInfoDTO(BaseDTO):
    id: int
    uid: int
    username: str
    nickname: str
    gender: int
    avatar: str
    email: Optional[str]
    mobile: Optional[str]
    wechat: Optional[str]
    occupation: str
    summary: str
    background: str
    address: str
    user_restriction: UserRestrictionDTO
    user_tag: int
    # 喜欢文章id列表
    article_like_set: list[int] = Field(default=[])
    # 点赞文章id列表
    article_collect_set: list[int] = Field(default=[])
    # 点赞评论id列表
    comment_like_set: list[int] = Field(default=[])
    user_settings: UserSettingsType = None


class UserCommonInfoDTO(BaseDTO):
    id: int
    uid: int
    nickname: str
    gender: int
    avatar: str
    occupation: str
    summary: str
    background: str
    address: str
    # 注册时间戳, 用于前端计算展示
    register_timestamp: int = 0
    # 该用户文章数量
    article_count: int = 0
    # 该用户评论数量
    comment_count: int = 0
    # 该用户粉丝数量
    fans_count: int = 0
    # 访问量
    view_count: int = 0
    # (登录用户)是否关注该用户
    is_followed: bool = False
    # 该用户是否我(登录用户)的粉丝
    is_my_fans: bool = False
    # 是否是好友
    is_friend: bool = False
    # 是否拉黑
    is_blocked: bool = False
    # 该用户所有文章的访问数量
    article_view_count: int = 0
    # 该用户所有文章的评论数量
    article_comment_count: int = 0
    # 该用户所有文章的点赞数量
    article_like_me_count: int = 0
    # 该用户所有文章的收藏数
    article_collect_count: int = 0
    # 用户配置
    user_settings: UserSettingsType = None


class WechatScanResultEnum(IntEnum):
    # 0:未扫码 1:未绑定 2:已绑定 3:已过期
    NOT_SCAN = 0
    UNBIND = 1
    HAS_BIND = 2
    EXPIRED = 3


class WechatScanResultDTO(BaseDTO):
    status: WechatScanResultEnum = WechatScanResultEnum.NOT_SCAN
    token: Optional[str] = None


class UserBaseInfoDTO(BaseDTO):
    id: Optional[int] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[GenderEnum] = None
    summary: Optional[str] = None


class UserSimpleInfoDTO(BaseDTO):
    id: Optional[int] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
