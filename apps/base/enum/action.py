from enum import IntEnum


class ActionTypeEnum(IntEnum):
    """
    动作类型 1:点赞/喜欢 2:收藏 3:关注 4:访问量 5:黑名单
    """
    LIKE = 1
    COLLECT = 2
    FOLLOW = 3
    VIEW = 4
    BLACKLIST = 5


class ObjectTypeEnum(IntEnum):
    """
    对象类型 1:文章 2:评论 3:用户 4:分享 5:图片
    """
    ARTICLE = 1
    COMMENT = 2
    USER = 3
    SHARE = 4
    PICTURE = 5
