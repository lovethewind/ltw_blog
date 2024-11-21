import time

from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant
from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.enum.comment import CommentStatusEnum
from apps.base.models.action import Action, ActionCount
from apps.base.models.comment import Comment


class ArticleMethod:
    """
    文章相关方法
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def get_article_like_count(self, article_id: int) -> int:
        """
        文章点赞数
        :param article_id: 文章id
        :return:
        """
        key = str(article_id)
        ret = await self._redis.hget(RedisConstant.ARTICLE_LIKE_COUNT_MAP_KEY, key)
        if ret is None:
            ret = await Action.filter(obj_id=article_id, obj_type=ObjectTypeEnum.ARTICLE,
                                      action_type=ActionTypeEnum.LIKE, status=True).count()
            await self._redis.hset(RedisConstant.ARTICLE_LIKE_COUNT_MAP_KEY, key, str(ret))
        return int(ret)

    async def get_articles_like_count(self, article_ids: list[int]) -> int:
        """
        批量统计文章点赞数
        :param article_ids:
        :return:
        """
        return sum([await self.get_article_like_count(article_id) for article_id in article_ids])

    async def add_or_remove_article_like(self, user_id: int, article_id: int) -> bool:
        """
        点赞/取消点赞文章, 增加/减少文章点赞数
        :param user_id: 用户id
        :param article_id: 文章id
        :return: True 点赞 False 取消点赞
        """
        item_key = str(article_id)
        key = f"{RedisConstant.USER_LIKE_ARTICLE_ZSET_KEY}:{user_id}"
        score = await self._redis.zscore(key, item_key)
        if score is None:
            await self._redis.zadd(key, {item_key: time.time()})
            await self._redis.hincrby(RedisConstant.ARTICLE_LIKE_COUNT_MAP_KEY, item_key, 1)
            return True
        await self._redis.zrem(key, item_key)
        await self._redis.hincrby(RedisConstant.ARTICLE_LIKE_COUNT_MAP_KEY, item_key, -1)
        return False

    async def get_article_collect_count(self, article_id: int) -> int:
        """
        文章收藏数
        :param article_id: 文章id
        :return:
        """
        key = str(article_id)
        ret = await self._redis.hget(RedisConstant.ARTICLE_COLLECT_COUNT_MAP_KEY, key)
        if ret is None:
            ret = await Action.filter(obj_id=article_id, obj_type=ObjectTypeEnum.ARTICLE,
                                      action_type=ActionTypeEnum.COLLECT, status=True).count()
            await self._redis.hset(RedisConstant.ARTICLE_COLLECT_COUNT_MAP_KEY, key, str(ret))
        return int(ret)

    async def get_articles_collect_count(self, article_ids: list[int]) -> int:
        """
        批量统计文章收藏数
        :param article_ids:
        :return:
        """
        return sum([await self.get_article_collect_count(article_id) for article_id in article_ids])

    async def add_or_remove_article_collect(self, user_id: int, article_id: int) -> bool:
        """
        收藏/取消收藏文章, 增加/减少文章收藏数
        :param user_id: 用户id
        :param article_id: 文章id
        :return: True 收藏 False 取消收藏
        """
        item_key = str(article_id)
        key = f"{RedisConstant.USER_COLLECT_ARTICLE_ZSET_KEY}:{user_id}"
        score = await self._redis.zscore(key, item_key)
        if score is None:
            await self._redis.zadd(key, {item_key: time.time()})
            await self._redis.hincrby(RedisConstant.ARTICLE_COLLECT_COUNT_MAP_KEY, item_key, 1)
            return True
        await self._redis.zrem(key, item_key)
        await self._redis.hincrby(RedisConstant.ARTICLE_COLLECT_COUNT_MAP_KEY, item_key, -1)
        return False

    async def get_article_comment_count(self, article_id: int) -> int:
        """
        文章评论数
        :param article_id: 文章id
        :return:
        """
        key = str(article_id)
        ret = await self._redis.hget(RedisConstant.ARTICLE_COMMENT_COUNT_MAP_KEY, key)
        if ret is None:
            ret = await Comment.filter(obj_id=article_id, obj_type=ObjectTypeEnum.ARTICLE,
                                       status=CommentStatusEnum.PASS).count()
            await self._redis.hset(RedisConstant.ARTICLE_COMMENT_COUNT_MAP_KEY, key, str(ret))
        return int(ret)

    async def get_articles_comment_count(self, article_ids: list[int]) -> int:
        """
        批量统计文章评论数
        :param article_ids:
        :return:
        """
        return sum([await self.get_article_comment_count(article_id) for article_id in article_ids])

    async def incr_article_comment_count(self, article_id: int, count: int = 1) :
        """
        增加/减少文章评论数
        :param article_id: 文章id
        :param count: 负数表示减少
        :return:
        """
        await self._redis.hincrby(RedisConstant.ARTICLE_COMMENT_COUNT_MAP_KEY, str(article_id), count)

    async def get_article_view_count(self, article_id: int) -> int:
        """
        文章访问数
        :param article_id: 文章id
        :return:
        """
        key = str(article_id)
        ret = await self._redis.hget(RedisConstant.ARTICLE_VIEW_COUNT_MAP_KEY, key)
        if ret is None:
            ret = await (
                ActionCount.filter(obj_id=article_id, obj_type=ObjectTypeEnum.ARTICLE, action_type=ActionTypeEnum.VIEW)
                .first().values_list("count", flat=True)) or 0
            await self._redis.hset(RedisConstant.ARTICLE_VIEW_COUNT_MAP_KEY, key, str(ret))
        return int(ret)

    async def get_articles_view_count(self, article_ids: list[int]) -> int:
        """
        批量统计文章访问数
        :param article_ids:
        :return:
        """
        return sum([await self.get_article_view_count(article_id) for article_id in article_ids])

    async def incr_article_view_count(self, article_id: int) :
        ret = await self._redis.hincrby(RedisConstant.ARTICLE_VIEW_COUNT_MAP_KEY, str(article_id))
        return ret


    async def get_published_article(self, current: int, size: int) -> list[int]:
        """
        获取已发布文章列表
        :param current: 当前页
        :param size: 每页数量
        :return:
        """
        start = (current - 1) * size
        end = start + size
        ret = await self._redis.zrevrange(RedisConstant.ARTICLE_PUBLISHED_VIEW_COUNT_ZSET_KEY, start, end)
        ret = [int(article_id) for article_id in ret]
        return ret

    async def add_published_article(self, article_id: int, view_count: int) :
        """
        添加已发布文章
        :param article_id: 文章id
        :param view_count:
        :return:
        """
        await self._redis.zadd(RedisConstant.ARTICLE_VIEW_COUNT_ADD_WAIT_KEY, {str(article_id): view_count})

    async def delete_published_article(self, article_id: int) :
        """
        移除已发布转为其他状态的文章
        :param article_id: 文章id
        :return:
        """
        await self._redis.zrem(RedisConstant.ARTICLE_VIEW_COUNT_ADD_WAIT_KEY, str(article_id))
