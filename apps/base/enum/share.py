from enum import IntEnum


class ShareTypeEnum(IntEnum):
    """
    分享类型 1：笔记 2：生活 3：经验 4：音乐 5：视频 6：资源 7：其他
    """
    NOTE = 1
    LIFE = 2
    EXPERIENCE = 3
    MUSIC = 4
    VIDEO = 5
    RESOURCE = 6
    OTHER = 7
