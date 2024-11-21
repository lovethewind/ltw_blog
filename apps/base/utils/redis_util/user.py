from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant
from apps.base.core.depend_inject import logger
from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.models.action import Action


class UserMethod:
    """
    用户相关方法
    """

    def __init__(self, redis: Redis):
        self._redis = redis
        self._inited = False

    async def init(self):
        key = f"{RedisConstant.USER_UID_GENERATOR_KEY}"
        ret = await self._redis.get(key)
        if not ret:
            logger.info(f"init user uid default value to 10000.")
            await self._redis.set(key, 10000)
        self._inited = True

    async def gen_uid(self):
        """
        生成用户uid
        :return:
        """
        if not self._inited:
            await self.init()
        key = f"{RedisConstant.USER_UID_GENERATOR_KEY}"
        return await self._redis.incr(key)

    async def add_view_count(self, user_id: int):
        """
        增加用户访问量
        :param user_id: 用户id
        :return: 新浏览次数
        """
        ret = await self._redis.hincrby(RedisConstant.USER_VIEW_COUNT_MAP_KEY, str(user_id))
        return ret

    async def get_view_count(self, user_id: int):
        """
         获取用户访问量
        :param user_id:
        :return:
        """
        ret = await self._redis.hget(RedisConstant.USER_VIEW_COUNT_MAP_KEY, str(user_id))
        return int(ret) if ret else 0

    async def get_user_error_count(self, user_id: int):
        key = f"{RedisConstant.USER_ERROR_COUNT_KEY}:{user_id}"
        ret = await self._redis.get(key) or 0
        return int(ret)

    async def incr_user_error_count(self, user_id: int, ex: int = 60 * 30):
        """
        增加用户错误次数
        :param user_id: 用户id
        :param ex: 过期时间
        :return: 新错误次数
        """
        key = f"{RedisConstant.USER_ERROR_COUNT_KEY}:{user_id}"
        if not await self._redis.exists(key):
            await self._redis.set(key, 0, ex=ex)
        ret = await self._redis.incr(key)
        return ret

    async def delete_user_error_count(self, user_id: int):
        """
        删除用户错误次数
        :param user_id: 用户id
        """
        key = f"{RedisConstant.USER_ERROR_COUNT_KEY}:{user_id}"
        await self._redis.delete(key)

    async def add_unlock_key(self, key: str, value: int):
        """
        存储解除封禁限制的key
        :param key:
        :param value:
        :return:
        """
        key = f"{RedisConstant.USER_UNBLOCK_KEY}:{key}"
        await self._redis.set(key, value=value, ex=30 * 60)

    async def get_unlock_key(self, key: str) -> list[int] | None:
        """
        检查解除封禁限制的key
        :param key:
        :return:
        """
        key = f"{RedisConstant.USER_UNBLOCK_KEY}:{key}"
        ret = await self._redis.get(key)
        if ret:
            return [int(item) for item in ret.split(":")]

    async def delete_unlock_key(self, key: str):
        """
        删除解除封禁限制的key
        :param key:
        :return:
        """
        key = f"{RedisConstant.USER_UNBLOCK_KEY}:{key}"
        await self._redis.delete(key)

    async def get_user_collect_articles(self, user_id: int):
        """
        获取用户收藏的文章集合
        :param user_id: 用户id
        :return: 文章id集合
        """
        key = f"{RedisConstant.USER_COLLECT_ARTICLE_ZSET_KEY}:{user_id}"
        if not await self._redis.exists(key):
            collects = await (Action.filter(user_id=user_id, obj_type=ObjectTypeEnum.ARTICLE,
                                            action_type=ActionTypeEnum.COLLECT, status=True)
                              .values("obj_id", "create_time"))
            collects_map = {collect["obj_id"]: collect["create_time"].timestamp() for collect in collects}
            if collects:
                await self._redis.zadd(key, collects_map)
        ret = await self._redis.zrange(key, 0, -1)
        ret = [int(article_id) for article_id in ret]
        return ret

    async def is_collect_article(self, user_id: int, article_id: int) -> bool:
        """
        用户是否已收藏该文章
        :param user_id:
        :param article_id:
        :return:
        """
        key = f"{RedisConstant.USER_COLLECT_ARTICLE_ZSET_KEY}:{user_id}"
        ret = await self._redis.zscore(key, article_id)
        return ret is not None

    async def get_user_like_articles(self, user_id: int):
        """
        获取用户点赞的文章集合
        :param user_id: 用户id
        :return: 文章id集合
        """
        key = f"{RedisConstant.USER_LIKE_ARTICLE_ZSET_KEY}:{user_id}"
        if not await self._redis.exists(key):
            likes = await (Action.filter(user_id=user_id, obj_type=ObjectTypeEnum.ARTICLE,
                                         action_type=ActionTypeEnum.LIKE, status=True)
                           .values("obj_id", "create_time"))
            likes_map = {like["obj_id"]: like["create_time"].timestamp() for like in likes}
            if likes_map:
                await self._redis.zadd(key, likes_map)
        ret = await self._redis.zrange(key, 0, -1)
        ret = [int(article_id) for article_id in ret]
        return ret

    async def has_like_article(self, user_id: int, article_id: int):
        """
        用户是否已点赞该文章
        :param user_id:
        :param article_id:
        :return:
        """
        key = f"{RedisConstant.USER_LIKE_ARTICLE_ZSET_KEY}:{user_id}"
        ret = await self._redis.zscore(key, article_id)
        return ret is not None

    async def get_user_like_comments(self, user_id: int):
        """
        获取用户点赞的评论集合
        :param user_id: 用户id
        :return: 文章id集合
        """
        key = f"{RedisConstant.USER_LIKE_COMMENT_ZSET_KEY}:{user_id}"
        if not await self._redis.exists(key):
            likes = await (Action.filter(user_id=user_id, obj_type=ObjectTypeEnum.COMMENT,
                                         action_type=ActionTypeEnum.LIKE, status=True)
                           .values("obj_id", "create_time"))
            likes_map = {like["obj_id"]: like["create_time"].timestamp() for like in likes}
            if likes_map:
                await self._redis.zadd(key, likes_map)
        ret = await self._redis.zrange(key, 0, -1)
        ret = [int(comment_id) for comment_id in ret]
        return ret

    async def has_like_comment(self, user_id: int, comment_id: int):
        """
        用户是否已点赞该评论
        :param user_id:
        :param comment_id:
        :return:
        """
        key = f"{RedisConstant.USER_LIKE_COMMENT_ZSET_KEY}:{user_id}"
        ret = await self._redis.zscore(key, comment_id)
        return ret is not None
