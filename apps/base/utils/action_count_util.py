from dataclasses import dataclass
from enum import IntEnum

from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant


@dataclass(frozen=True)
class ActionCountDirtyItem:
    """
    行为计数 dirty 项。

    :param redis_hash_key: Redis hash 键。
    :param obj_type: 对象类型。
    :param action_type: 行为类型。
    :param obj_id: 对象 ID。
    """

    redis_hash_key: str
    obj_type: int
    action_type: int
    obj_id: int


def build_action_count_dirty_member(
    redis_hash_key: str,
    obj_type: int | IntEnum,
    action_type: int | IntEnum,
    obj_id: int | str,
) -> str:
    """
    构建行为计数 dirty 集合成员。

    :param redis_hash_key: Redis hash 键。
    :param obj_type: 对象类型。
    :param action_type: 行为类型。
    :param obj_id: 对象 ID。
    :return: dirty 集合成员字符串。
    """
    return f"{redis_hash_key}:{int(obj_type)}:{int(action_type)}:{int(obj_id)}"


def parse_action_count_dirty_member(member: str) -> ActionCountDirtyItem | None:
    """
    解析行为计数 dirty 集合成员。

    :param member: dirty 集合成员字符串。
    :return: dirty 项；格式无效时返回 None。
    """
    parts = member.split(":", 3)
    if len(parts) != 4:
        return None
    redis_hash_key, obj_type, action_type, obj_id = parts
    try:
        return ActionCountDirtyItem(
            redis_hash_key=redis_hash_key,
            obj_type=int(obj_type),
            action_type=int(action_type),
            obj_id=int(obj_id),
        )
    except ValueError:
        return None


async def mark_action_count_dirty(
    redis: Redis,
    redis_hash_key: str,
    obj_type: int | IntEnum,
    action_type: int | IntEnum,
    obj_id: int | str,
) -> None:
    """
    标记行为计数需要同步到数据库。

    :param redis: Redis 客户端。
    :param redis_hash_key: Redis hash 键。
    :param obj_type: 对象类型。
    :param action_type: 行为类型。
    :param obj_id: 对象 ID。
    :return: None。
    """
    member = build_action_count_dirty_member(redis_hash_key, obj_type, action_type, obj_id)
    await redis.sadd(RedisConstant.ACTION_COUNT_DIRTY_SET_KEY, member)
