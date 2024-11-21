# @Time    : 2024/11/4 16:41
# @Author  : frank
# @File    : event_name.py
from enum import StrEnum


class EventName(StrEnum):
    UPDATE_USER_INFO = "update_user_info"
    UPDATE_GROUP_INFO = "update_group_info"
