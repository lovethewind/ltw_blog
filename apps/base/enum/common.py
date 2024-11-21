from enum import IntEnum, StrEnum


class CheckStatusEnum(IntEnum):
    """
    审核状态: 1: 已通过 2:审核中 3:拒绝
    """
    PASS = 1
    CHECKING = 2
    REJECT = 3


class VerifyCodeTypeEnum(StrEnum):
    """
    验证码类型: register、find_password、change_bind、login、change_password
    """
    REGISTER = "register"
    FIND_PASSWORD = "find_password"
    CHANGE_BIND = "change_bind"
    LOGIN = "login"
    CHANGE_PASSWORD = "change_password"


class FeedbackTypeEnum(IntEnum):
    """
    反馈类型: 1: 提交需求 2: 反馈bug
    """
    REQUIREMENT = 1
    BUG = 2
