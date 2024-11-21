# @Time    : 2024/10/22 17:15
# @Author  : frank
# @File    : share.py

import asyncio
from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant


class ShareMethod:
    """
    分享方法
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def has_like(self, user_id: int, share_id: int) -> bool:
        """
        判断是否点赞
        :param user_id:
        :param share_id:
        :return:
        """
        key = f"{RedisConstant.USER_LIKE_SHARE_SET_KEY}:{user_id}"
        return bool(await self._redis.sismember(key, str(share_id)))

    async def get_like_count(self, share_id: int):
        """
        获取点赞数量
        :param share_id:
        :return:
        """
        ret = await self._redis.hget(RedisConstant.SHARE_LIKE_COUNT_MAP_KEY, str(share_id))
        return int(ret) if ret else 0

    async def add_or_remove_share_like(self, user_id: int, share_id: int):
        """
        添加或移除
        :param user_id:
        :param share_id:
        :return:
        """
        user_id = str(user_id)
        share_id = str(share_id)
        key = f"{RedisConstant.USER_LIKE_SHARE_SET_KEY}:{user_id}"
        if await self._redis.sismember(key, share_id):
            await asyncio.gather(
                self._redis.srem(key, share_id),
                self._redis.hincrby(RedisConstant.SHARE_LIKE_COUNT_MAP_KEY, share_id, -1),  # 数量减1
            )
            return False
        await asyncio.gather(
            self._redis.sadd(key, share_id),
            self._redis.hincrby(RedisConstant.SHARE_LIKE_COUNT_MAP_KEY, share_id),  # 数量加1
        )
        return True
