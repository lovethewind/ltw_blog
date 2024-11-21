# @Time    : 2024/10/21 16:13
# @Author  : frank
# @File    : notice.py
from enum import IntEnum


class NoticeTypeEnum(IntEnum):
    """
    1: 系统 2: 评论 3:回复(评论) 4: @我 5: 点赞 6: 收藏 7: 关注
    """
    SYSTEM = 1
    COMMENT = 2
    REPLY = 3
    AT = 4
    LIKE = 5
    COLLECT = 6
    FOLLOW = 7
