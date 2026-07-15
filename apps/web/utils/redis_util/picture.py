# @Time    : 2024/10/22 17:25
# @Author  : frank
# @File    : picture.py

import asyncio

from redis.asyncio import Redis
from sqlalchemy import select

from apps.base.constant.redis_constant import RedisConstant
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.models.action import Action, ActionCount
from apps.base.utils.action_count_util import mark_action_count_dirty


class PictureMethod:
    """
    图片方法
    """

    EMPTY_MEMBER = "__empty__"

    def __init__(self, redis: Redis):
        self._redis = redis

    async def _ensure_like_cache(self, user_id: int) -> None:
        """
        确保指定用户的图片点赞集合缓存已初始化。

        :param user_id: 用户 ID。
        :return: None。
        """
        key = f"{RedisConstant.USER_LIKE_PICTURE_SET_KEY}:{user_id}"
        if await self._redis.exists(key):
            return
        picture_ids = await db.model_all(
            select(Action.obj_id).where(
                Action.user_id == user_id,
                Action.obj_type == ObjectTypeEnum.PICTURE,
                Action.action_type == ActionTypeEnum.LIKE,
                Action.status.is_(True),
            )
        )
        await self._redis.sadd(key, self.EMPTY_MEMBER, *(str(picture_id) for picture_id in picture_ids))

    async def has_like(self, user_id: int, picture_id: int) -> bool:
        """
        判断是否点赞
        :param user_id:
        :param picture_id:
        :return:
        """
        key = f"{RedisConstant.USER_LIKE_PICTURE_SET_KEY}:{user_id}"
        await self._ensure_like_cache(user_id)
        return bool(await self._redis.sismember(key, str(picture_id)))

    async def get_like_count(self, picture_id: int) -> int:
        """
        获取点赞数量
        :param picture_id: 图片 ID。
        :return: 点赞数量。
        """
        key = str(picture_id)
        ret = await self._redis.hget(RedisConstant.PICTURE_LIKE_COUNT_MAP_KEY, key)
        if ret is None:
            ret = (
                await db.scalar(
                    select(ActionCount.count).where(
                        ActionCount.obj_id == picture_id,
                        ActionCount.obj_type == ObjectTypeEnum.PICTURE,
                        ActionCount.action_type == ActionTypeEnum.LIKE,
                    )
                )
                or 0
            )
            await self._redis.hset(RedisConstant.PICTURE_LIKE_COUNT_MAP_KEY, key, str(ret))
        return int(ret)

    async def add_or_remove_picture_like(self, user_id: int, picture_id: int) -> bool:
        """
        添加或移除
        :param user_id:
        :param picture_id:
        :return:
        """
        await self._ensure_like_cache(user_id)
        await self.get_like_count(picture_id)
        user_id = str(user_id)
        picture_id = str(picture_id)
        key = f"{RedisConstant.USER_LIKE_PICTURE_SET_KEY}:{user_id}"
        if bool(await self._redis.sismember(key, picture_id)):
            await asyncio.gather(
                self._redis.srem(key, picture_id),
                self._redis.hincrby(RedisConstant.PICTURE_LIKE_COUNT_MAP_KEY, picture_id, -1),  # 数量减1
            )
            await mark_action_count_dirty(
                self._redis,
                RedisConstant.PICTURE_LIKE_COUNT_MAP_KEY,
                ObjectTypeEnum.PICTURE,
                ActionTypeEnum.LIKE,
                picture_id,
            )
            return False
        await asyncio.gather(
            self._redis.sadd(key, picture_id),
            self._redis.hincrby(RedisConstant.PICTURE_LIKE_COUNT_MAP_KEY, picture_id),  # 数量加1
        )
        await mark_action_count_dirty(
            self._redis,
            RedisConstant.PICTURE_LIKE_COUNT_MAP_KEY,
            ObjectTypeEnum.PICTURE,
            ActionTypeEnum.LIKE,
            picture_id,
        )
        return True
