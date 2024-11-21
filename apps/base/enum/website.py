# @Time    : 2024/9/1 23:12
# @Author  : frank
# @File    : website.py
from enum import IntEnum


class WebsiteStatusEnum(IntEnum):
    """
    PASS(1, "已通过"),
    CHECK(2, "审核中"),
    REJECT(3, "拒绝");
    """
    PASS = 1
    CHECK = 2
    REJECT = 3
