# @Time    : 2024/10/16 16:00
# @Author  : frank
# @File    : oss.py
from enum import Enum


class DirTypeItem:

    def __init__(self, dir_name, content_type, max_size, expire_seconds):
        """
        :param dir_name: 目录名
        :param content_type: 文件类型
        :param max_size: 文件大小限制(M)
        :param expire_seconds: 过期时间
        """
        self.dir = dir_name
        self.content_type = content_type
        self.max_size = max_size
        self.expire_seconds = expire_seconds


class DirType(Enum):
    AVATAR = DirTypeItem("media/avatar/", "image/*", 5, 10)
    BACKGROUND = DirTypeItem("media/background/", "image/*", 20, 20)
    COVER = DirTypeItem("media/cover/", "image/*", 10, 20)
    EMOJI = DirTypeItem("media/emoji/", "image/*", 5, 10)
    IMAGE = DirTypeItem("media/image/", "image/*", 20, 20)
    AUDIO = DirTypeItem("media/audio/", "audio/*", 50, 20)
    VIDEO = DirTypeItem("media/video/", "video/*", 200, 30)
    ATTACH = DirTypeItem("media/attach/", "*/*", 1024, 30)
    OTHER = DirTypeItem("media/other/", "*/*", 1024, 30)
