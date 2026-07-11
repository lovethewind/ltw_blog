# @Time    : 2024/11/6 15:17
# @Author  : frank
# @File    : chat.py
from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant


class ChatMethod:
    """
    文章相关方法
    """

    EMPTY_MEMBER = "__empty__"

    def __init__(self, redis: Redis):
        self._redis = redis

    def _contact_key(self, user_id: int) -> str:
        """
        获取用户联系人缓存键。

        :param user_id: 用户 ID
        :return: Redis 联系人集合键
        """
        return f"{RedisConstant.USER_CONTACT_SET_KEY}:{user_id}"

    def _blacklist_key(self, user_id: int) -> str:
        """
        获取用户黑名单缓存键。

        :param user_id: 用户 ID
        :return: Redis 黑名单集合键
        """
        return f"{RedisConstant.USER_BLACKLIST_SET_KEY}:{user_id}"

    async def has_contact_cache(self, user_id: int) -> bool:
        """
        判断用户联系人缓存是否存在。

        :param user_id: 用户 ID
        :return: 联系人缓存是否存在
        """
        return bool(await self._redis.exists(self._contact_key(user_id)))

    async def is_friend(self, user_id: int, contact_id: int) -> bool:
        """
        判断联系人是否在用户好友缓存中。

        :param user_id: 用户 ID
        :param contact_id: 联系人 ID
        :return: 是否是好友
        """
        return bool(await self._redis.sismember(self._contact_key(user_id), str(contact_id)))

    async def refresh_user_contacts(self, user_id: int, contact_ids: list[int]) -> None:
        """
        刷新用户联系人缓存。

        :param user_id: 用户 ID
        :param contact_ids: 联系人 ID 列表
        :return: None
        """
        key = self._contact_key(user_id)
        await self._redis.delete(key)
        await self._redis.sadd(key, self.EMPTY_MEMBER, *(str(contact_id) for contact_id in contact_ids))

    async def add_contact(self, user_id: int, contact_id: int) -> None:
        """
        在联系人缓存存在时添加联系人。

        :param user_id: 用户 ID
        :param contact_id: 联系人 ID
        :return: None
        """
        key = self._contact_key(user_id)
        if await self._redis.exists(key):
            await self._redis.sadd(key, str(contact_id))

    async def remove_contact(self, user_id: int, contact_id: int) -> None:
        """
        在联系人缓存存在时移除联系人。

        :param user_id: 用户 ID
        :param contact_id: 联系人 ID
        :return: None
        """
        key = self._contact_key(user_id)
        if await self._redis.exists(key):
            await self._redis.srem(key, str(contact_id))

    async def has_blacklist_cache(self, user_id: int) -> bool:
        """
        判断用户黑名单缓存是否存在。

        :param user_id: 用户 ID
        :return: 黑名单缓存是否存在
        """
        return bool(await self._redis.exists(self._blacklist_key(user_id)))

    async def is_blocked(self, user_id: int, contact_id: int) -> bool:
        """
        判断联系人是否在用户黑名单缓存中。

        :param user_id: 用户 ID
        :param contact_id: 联系人 ID
        :return: 是否已拉黑
        """
        return bool(await self._redis.sismember(self._blacklist_key(user_id), str(contact_id)))

    async def refresh_user_blacklist(self, user_id: int, contact_ids: list[int]) -> None:
        """
        刷新用户黑名单缓存。

        :param user_id: 用户 ID
        :param contact_ids: 黑名单用户 ID 列表
        :return: None
        """
        key = self._blacklist_key(user_id)
        await self._redis.delete(key)
        await self._redis.sadd(key, self.EMPTY_MEMBER, *(str(contact_id) for contact_id in contact_ids))

    async def sync_blacklist(self, user_id: int, contact_id: int, status: bool) -> None:
        """
        在黑名单缓存存在时同步单个黑名单状态。

        :param user_id: 用户 ID
        :param contact_id: 被拉黑用户 ID
        :param status: 是否拉黑
        :return: None
        """
        key = self._blacklist_key(user_id)
        if not await self._redis.exists(key):
            return
        if status:
            await self._redis.sadd(key, str(contact_id))
            return
        await self._redis.srem(key, str(contact_id))

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
