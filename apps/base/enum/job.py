from enum import IntEnum


class MisfirePolicyEnum(IntEnum):
    """
    计划执行策略（1:立即执行 2:执行一次 3:放弃执行）
    """
    IMMEDIATELY = 1
    EXECUTE_ONCE = 2
    ABANDON = 3


class JobStatusEnum(IntEnum):
    """
    任务状态（1:正常 2:暂停）
    """
    NORMAL = 1
    PAUSE = 2
