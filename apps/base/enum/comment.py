from enum import IntEnum


class CommentStatusEnum(IntEnum):
    """
    1:通过 2:审核中 3:已删除
    """
    PASS = 1
    CHECKING = 2
    DELETE = 3
