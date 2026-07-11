import time

from redis.asyncio import Redis
from sqlalchemy import func, select

from apps.base.constant.redis_constant import RedisConstant
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.models.action import Action
from apps.web.utils.redis_util.action_count import mark_action_count_dirty


class CommentMethod:
    """
    评论相关方法
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def get_comment_like_count(self, comment_id: int) -> int:
        """
        评论点赞数

        :param comment_id: 评论id。
        :return: 评论点赞数。
        """
        key = str(comment_id)
        ret = await self._redis.hget(RedisConstant.COMMENT_LIKE_COUNT_MAP_KEY, key)
        if ret is None:
            ret = await db.scalar(
                select(func.count(Action.id)).where(
                    Action.obj_id == comment_id,
                    Action.obj_type == ObjectTypeEnum.COMMENT,
                    Action.action_type == ActionTypeEnum.LIKE,
                    Action.status.is_(True),
                )
            )
            await self._redis.hset(RedisConstant.COMMENT_LIKE_COUNT_MAP_KEY, key, str(ret))
        return int(ret)

    async def get_comments_like_count(self, comment_ids: list[int]) -> int:
        """
        批量统计评论点赞数
        :param comment_ids:
        :return:
        """
        return sum([await self.get_comment_like_count(comment_id) for comment_id in comment_ids])

    async def add_or_remove_comment_like(self, user_id: int, article_id: int) -> bool:
        """
        点赞/取消点赞评论
        :param user_id: 用户id
        :param article_id: 评论id
        :return: True 点赞 False 取消点赞
        """
        item_key = str(article_id)
        key = f"{RedisConstant.USER_LIKE_COMMENT_ZSET_KEY}:{user_id}"
        score = await self._redis.zscore(key, item_key)
        if score is None:
            await self._redis.zadd(key, {item_key: time.time()})
            await self._redis.hincrby(RedisConstant.COMMENT_LIKE_COUNT_MAP_KEY, item_key, 1)
            await mark_action_count_dirty(
                self._redis,
                RedisConstant.COMMENT_LIKE_COUNT_MAP_KEY,
                ObjectTypeEnum.COMMENT,
                ActionTypeEnum.LIKE,
                article_id,
            )
            return True
        await self._redis.zrem(key, item_key)
        await self._redis.hincrby(RedisConstant.COMMENT_LIKE_COUNT_MAP_KEY, item_key, -1)
        await mark_action_count_dirty(
            self._redis,
            RedisConstant.COMMENT_LIKE_COUNT_MAP_KEY,
            ObjectTypeEnum.COMMENT,
            ActionTypeEnum.LIKE,
            article_id,
        )
        return False
