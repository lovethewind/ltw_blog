from enum import IntEnum, StrEnum


class GenderEnum(IntEnum):
    SECRET = 0
    MALE = 1
    FEMALE = 2


class UserTagEnum(IntEnum):
    SUPER_ADMIN = 0
    ADMIN = 1
    NORMAL_USER = 2
    OTHER = 3


class MenuTypeEnum(IntEnum):
    CATALOG = 0
    MENU = 1
    BUTTON = 2


class UserRestrictionTypeEnum(IntEnum):
    """
    1:禁止登录 2:禁止评论
    """
    BAN = 1
    MUTE = 2


class WechatCodeTypeEnum(IntEnum):
    """
    1:登录 2:换绑旧验证 3:新绑定 4:修改密码
    """
    LOGIN = 1
    CHANGE_BIND_OLD = 2
    CHANGE_BIND_NEW = 3
    CHANGE_PASSWORD = 4


class UserSettingsEnum(StrEnum):
    """
    allowViewMyCollect:允许查看我的收藏
    allowViewMyFollow:允许查看我的关注/粉丝
    allowViewMyArticle:允许查看我的文章
    whenCommentMyContent:评论我的内容时
    whenReplyMyComment:回复我的评论时
    whenLikeMyContent:点赞我的内容时
    whenCollectMyContent:收藏我的内容时
    whenFollowMe:关注我时
    """
    ALLOW_VIEW_MY_COLLECT = "allowViewMyCollect"
    ALLOW_VIEW_MY_FOLLOW = "allowViewMyFollow"
    ALLOW_VIEW_MY_ARTICLE = 'allowViewMyArticle'
    WHEN_COMMENT_MY_CONTENT = 'whenCommentMyContent'
    WHEN_REPLY_MY_COMMENT = 'whenReplyMyComment'
    WHEN_LIKE_MY_CONTENT = 'whenLikeMyContent'
    WHEN_COLLECT_MY_CONTENT = 'whenCollectMyContent'
    WHEN_FOLLOW_ME = 'whenFollowMe'
