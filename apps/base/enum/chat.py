# @Time    : 2024/11/4 14:01
# @Author  : frank
# @File    : chat_dto.py
from enum import IntEnum


class WSMessageTypeEnum(IntEnum):
    NOTICE = 1
    CHAT_MESSAGE = 2
    SYSTEM_IN_TIME = 3
    CHANGE_CURRENT_CONVERSATION = 4
    FRIEND_APPLY = 5


class WSMessageShowType(IntEnum):
    NOTIFICATION = 1
    MESSAGEBOX = 2


class ContactTypeEnum(IntEnum):
    USER = 1
    GROUP = 2


class ChatMessageTypeEnum(IntEnum):
    SYSTEM = 1
    TEXT = 2
    IMAGE = 3
    AUDIO = 4
    VIDEO = 5
    FILE = 6
    REPLY = 7
    AT = 8


class ChatGroupRoleEnum(IntEnum):
    ADMIN = 1
    MEMBER = 2


class ChatGroupTypeEnum(IntEnum):
    PRIVATE = 1
    PUBLIC = 2


class ChatGroupJoinTypeEnum(IntEnum):
    SEARCH = 1
    INVITE = 2


class MessageSendStatusEnum(IntEnum):
    SENDING = 1
    SUCCESS = 2
    FAIL = 3
    DELETE = 4


class ContactApplyStatusEnum(IntEnum):
    PENDING = 1
    AGREE = 2
    REFUSE = 3
