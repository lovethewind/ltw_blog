import asyncio

from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant


class ActionMethod:
    """
    用户行为相关方法
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def is_followed(self, user_id: int, follower_id: int) -> bool:
        """
        判断是否已关注
        :param user_id: 用户id
        :param follower_id: 粉丝id
        :return: 是否已关注
        """
        key = f"{RedisConstant.USER_FOLLOWER_SET_KEY}:{user_id}"
        return bool(await self._redis.sismember(key, str(follower_id)))

    async def is_fans(self, user_id: int, follower_id: int) -> bool:
        """
        判断是否是粉丝
        :param user_id: 用户id
        :param follower_id: 粉丝id
        :return: 是否是粉丝
        """
        key = f"{RedisConstant.USER_FOLLOWER_SET_KEY}:{follower_id}"
        return bool(await self._redis.sismember(key, str(user_id)))

    async def get_fans_count(self, user_id: int) -> int:
        """
        获取某用户粉丝数量
        :param user_id: 用户id
        :return: 粉丝数量
        """
        ret = await self._redis.hget(RedisConstant.USER_FANS_COUNT_MAP_KEY, str(user_id)) or 0
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
                self._redis.hincrby(RedisConstant.USER_FANS_COUNT_MAP_KEY, str(follower_id), -1)  # 该用户的粉丝数量减1
            )
            return False
        await asyncio.gather(
            self._redis.sadd(key, str(follower_id)),
            self._redis.hincrby(RedisConstant.USER_FOLLOWER_COUNT_MAP_KEY, str(user_id)),  # 我关注的数量加1
            self._redis.hincrby(RedisConstant.USER_FANS_COUNT_MAP_KEY, str(follower_id))  # 该用户的粉丝数量加1
        )
        return True
