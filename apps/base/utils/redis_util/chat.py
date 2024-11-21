# @Time    : 2024/11/6 15:17
# @Author  : frank
# @File    : chat.py
from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant


class ChatMethod:
    """
    文章相关方法
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def get_conversation_unread_count(self, user_id: int, conversation_id: str) -> int:
        """
        获取会话未读数量
        :param user_id:
        :param conversation_id:
        :return:
        """
        key = f"{user_id}:{conversation_id}"
        ret = await self._redis.hget(RedisConstant.CONVERSATION_UNREAD_COUNT_MAP_KEY, key)
        return int(ret) if ret is not None else 0

    async def incr_conversation_unread_count(self, user_id: int, conversation_id: str) -> int:
        """
        增加会话未读数量
        :param user_id:
        :param conversation_id:
        :return:
        """
        key = f"{user_id}:{conversation_id}"
        return await self._redis.hincrby(RedisConstant.CONVERSATION_UNREAD_COUNT_MAP_KEY, key, 1)

    async def reset_conversation_unread_count(self, user_id: int, conversation_id: str) -> int:
        """
        重置会话未读数量
        :param user_id:
        :param conversation_id:
        :return:
        """
        key = f"{user_id}:{conversation_id}"
        await self._redis.hset(RedisConstant.CONVERSATION_UNREAD_COUNT_MAP_KEY, key, "0")
        return 0
