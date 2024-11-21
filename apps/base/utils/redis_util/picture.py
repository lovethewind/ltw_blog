# @Time    : 2024/10/22 17:25
# @Author  : frank
# @File    : picture.py

import asyncio
from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant


class PictureMethod:
    """
    图片方法
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def has_like(self, user_id: int, picture_id: int) -> bool:
        """
        判断是否点赞
        :param user_id:
        :param picture_id:
        :return:
        """
        key = f"{RedisConstant.USER_LIKE_PICTURE_SET_KEY}:{user_id}"
        return bool(await self._redis.sismember(key, str(picture_id)))

    async def get_like_count(self, picture_id: int):
        """
        获取点赞数量
        :param picture_id:
        :return:
        """
        ret = await self._redis.hget(RedisConstant.PICTURE_LIKE_COUNT_MAP_KEY, str(picture_id))
        return int(ret) if ret else 0

    async def add_or_remove_picture_like(self, user_id: int, picture_id: int):
        """
        添加或移除
        :param user_id:
        :param picture_id:
        :return:
        """
        user_id = str(user_id)
        picture_id = str(picture_id)
        key = f"{RedisConstant.USER_LIKE_PICTURE_SET_KEY}:{user_id}"
        if bool(await self._redis.sismember(key, picture_id)):
            await asyncio.gather(
                self._redis.srem(key, picture_id),
                self._redis.zincrby(RedisConstant.PICTURE_LIKE_COUNT_ZSET_KEY, int(picture_id), -1),
                self._redis.hincrby(RedisConstant.PICTURE_LIKE_COUNT_MAP_KEY, picture_id, -1)  # 数量减1
            )
            return False
        await asyncio.gather(
            self._redis.sadd(key, picture_id),
            self._redis.zincrby(RedisConstant.PICTURE_LIKE_COUNT_ZSET_KEY, int(picture_id), 1),
            self._redis.hincrby(RedisConstant.PICTURE_LIKE_COUNT_MAP_KEY, picture_id)  # 数量加1
        )
        return True
