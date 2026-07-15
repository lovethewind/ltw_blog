import asyncio

from redis.asyncio import Redis
from sqlalchemy import func, select

from apps.base.constant.redis_constant import RedisConstant
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.models.action import Action


class ActionMethod:
    """
    用户行为相关方法
    """

    EMPTY_MEMBER = "__empty__"

    def __init__(self, redis: Redis):
        self._redis = redis

    async def _ensure_follow_cache(self, user_id: int) -> None:
        """
        确保指定用户的关注集合缓存已初始化。

        :param user_id: 用户 ID。
        :return: None。
        """
        key = f"{RedisConstant.USER_FOLLOWER_SET_KEY}:{user_id}"
        if await self._redis.exists(key):
            return
        follower_ids = await db.model_all(
            select(Action.obj_id).where(
                Action.user_id == user_id,
                Action.obj_type == ObjectTypeEnum.USER,
                Action.action_type == ActionTypeEnum.FOLLOW,
                Action.status.is_(True),
            )
        )
        await self._redis.sadd(key, self.EMPTY_MEMBER, *(str(follower_id) for follower_id in follower_ids))

    async def is_followed(self, user_id: int, target_id: int) -> bool:
        """
        判断用户是否已关注对方
        :param user_id: 用户id
        :param target_id: 对方id
        :return: 是否已关注
        """
        key = f"{RedisConstant.USER_FOLLOWER_SET_KEY}:{user_id}"
        await self._ensure_follow_cache(user_id)
        return bool(await self._redis.sismember(key, str(target_id)))

    async def is_fans(self, user_id: int, target_id: int) -> bool:
        """
        判断对方是否是自己的粉丝
        :param user_id: 用户id
        :param target_id: 对方id
        :return: 是否是粉丝
        """
        key = f"{RedisConstant.USER_FOLLOWER_SET_KEY}:{target_id}"
        await self._ensure_follow_cache(target_id)
        return bool(await self._redis.sismember(key, str(user_id)))

    async def get_fans_count(self, user_id: int) -> int:
        """
        获取某用户粉丝数量
        :param user_id: 用户id
        :return: 粉丝数量
        """
        key = str(user_id)
        ret = await self._redis.hget(RedisConstant.USER_FANS_COUNT_MAP_KEY, key)
        if ret is None:
            ret = await db.scalar(
                select(func.count(Action.id)).where(
                    Action.obj_id == user_id,
                    Action.obj_type == ObjectTypeEnum.USER,
                    Action.action_type == ActionTypeEnum.FOLLOW,
                    Action.status.is_(True),
                )
            )
            await self._redis.hset(RedisConstant.USER_FANS_COUNT_MAP_KEY, key, str(ret))
        return int(ret)

    async def add_or_remove_follow(self, user_id: int, follower_id: int):
        """
        添加或移除关注
        :param user_id: 用户id
        :param follower_id: 粉丝id
        :return:
        """
        key = f"{RedisConstant.USER_FOLLOWER_SET_KEY}:{user_id}"
        if await self._redis.sismember(key, str(follower_id)):
            await asyncio.gather(
                self._redis.srem(key, str(follower_id)),
                self._redis.hincrby(RedisConstant.USER_FOLLOWER_COUNT_MAP_KEY, str(user_id), -1),  # 我关注的数量减1
                self._redis.hincrby(RedisConstant.USER_FANS_COUNT_MAP_KEY, str(follower_id), -1),  # 该用户的粉丝数量减1
            )
            return False
        await asyncio.gather(
            self._redis.sadd(key, str(follower_id)),
            self._redis.hincrby(RedisConstant.USER_FOLLOWER_COUNT_MAP_KEY, str(user_id)),  # 我关注的数量加1
            self._redis.hincrby(RedisConstant.USER_FANS_COUNT_MAP_KEY, str(follower_id)),  # 该用户的粉丝数量加1
        )
        return True
