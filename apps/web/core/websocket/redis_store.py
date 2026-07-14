import json
import time
from collections.abc import Callable
from typing import Any

from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant
from apps.base.core.depend_inject import GetBean
from apps.web.core.websocket.data import WebSocketEnvelope


class WebSocketRedisStore:
    """WebSocket 跨 worker 状态和消息的 Redis 存储。"""

    CHANNEL = "ws:message"
    CONNECTION_KEY_PREFIX = "ws:user:connections"
    CONNECTION_CONVERSATION_KEY = "ws:connection:conversation"
    USER_PROFILE_KEY_PREFIX = RedisConstant.USER_PROFILE_CACHE_KEY_PREFIX
    GROUP_PROFILE_KEY_PREFIX = "ws:group:profile"

    def __init__(
        self,
        redis_provider: Callable[[], Redis] | None = None,
        connection_ttl: int = 90,
        profile_ttl: int = 24 * 60 * 60,
        time_provider: Callable[[], float] = time.time,
    ) -> None:
        """
        初始化 Redis 状态仓库。

        :param redis_provider: Redis 客户端提供函数
        :param connection_ttl: 连接状态有效秒数
        :param profile_ttl: 用户和群组资料缓存秒数
        :param time_provider: 当前时间提供函数
        :return: None
        """
        self._redis_provider = redis_provider or self._get_default_redis
        self.connection_ttl = connection_ttl
        self.profile_ttl = profile_ttl
        self._time_provider = time_provider

    @staticmethod
    def _get_default_redis() -> Redis:
        """
        获取项目 Redis 客户端。

        :return: Redis 客户端
        """

        from apps.web.utils.redis_util import WebRedisUtil

        return GetBean(WebRedisUtil).redis

    def get_redis(self) -> Redis:
        """
        获取当前 Redis 客户端。

        :return: Redis 客户端
        """
        return self._redis_provider()

    def _connection_key(self, user_id: int) -> str:
        """
        生成用户连接集合键。

        :param user_id: 用户 ID
        :return: Redis 键
        """
        return f"{self.CONNECTION_KEY_PREFIX}:{user_id}"

    async def add_connection(self, user_id: int, connection_id: str) -> None:
        """
        添加或续期用户连接。

        :param user_id: 用户 ID
        :param connection_id: 连接 ID
        :return: None
        """
        expires_at = self._time_provider() + self.connection_ttl
        await self.get_redis().zadd(self._connection_key(user_id), {connection_id: expires_at})

    async def refresh_connections(self, connections: list[tuple[int, str]]) -> None:
        """
        批量续期本 worker 的连接。

        :param connections: 用户 ID 与连接 ID 列表
        :return: None
        """
        for user_id, connection_id in connections:
            await self.add_connection(user_id, connection_id)

    async def remove_connection(self, user_id: int, connection_id: str) -> None:
        """
        删除用户连接及其当前会话。

        :param user_id: 用户 ID
        :param connection_id: 连接 ID
        :return: None
        """
        redis = self.get_redis()
        await redis.zrem(self._connection_key(user_id), connection_id)
        await redis.hdel(self.CONNECTION_CONVERSATION_KEY, connection_id)

    async def set_current_conversation(
        self,
        user_id: int,
        connection_id: str,
        conversation_id: str,
    ) -> None:
        """
        设置连接当前停留的会话。

        :param user_id: 用户 ID
        :param connection_id: 连接 ID
        :param conversation_id: 会话 ID，空字符串表示离开会话
        :return: None
        """
        await self.add_connection(user_id, connection_id)
        redis = self.get_redis()
        if conversation_id:
            await redis.hset(self.CONNECTION_CONVERSATION_KEY, connection_id, conversation_id)
            return
        await redis.hdel(self.CONNECTION_CONVERSATION_KEY, connection_id)

    async def _prune_connections(self, user_id: int) -> list[str]:
        """
        清理并返回用户的有效连接。

        :param user_id: 用户 ID
        :return: 有效连接 ID 列表
        """
        redis = self.get_redis()
        key = self._connection_key(user_id)
        expired = await redis.zrangebyscore(key, float("-inf"), self._time_provider())
        if expired:
            await redis.zremrangebyscore(key, float("-inf"), self._time_provider())
            await redis.hdel(self.CONNECTION_CONVERSATION_KEY, *expired)
        return await redis.zrange(key, 0, -1)

    async def is_online(self, user_id: int) -> bool:
        """
        判断用户是否存在有效连接。

        :param user_id: 用户 ID
        :return: 是否在线
        """
        return bool(await self._prune_connections(user_id))

    async def is_in_conversation(self, user_id: int, conversation_id: str) -> bool:
        """
        判断用户是否有连接停留在指定会话。

        :param user_id: 用户 ID
        :param conversation_id: 会话 ID
        :return: 是否停留在会话中
        """
        connection_ids = await self._prune_connections(user_id)
        if not connection_ids:
            return False
        current_conversations = await self.get_redis().hmget(
            self.CONNECTION_CONVERSATION_KEY,
            connection_ids,
        )
        return conversation_id in current_conversations

    async def _set_profile(self, key: str, profile: dict[str, Any]) -> None:
        """
        缓存资料字典。

        :param key: Redis 键
        :param profile: 资料字典
        :return: None
        """
        await self.get_redis().set(
            key,
            json.dumps(profile, ensure_ascii=False, separators=(",", ":")),
            ex=self.profile_ttl,
        )

    async def _get_profile(self, key: str) -> dict[str, Any] | None:
        """
        获取资料字典。

        :param key: Redis 键
        :return: 资料字典，不存在时返回 None
        """
        value = await self.get_redis().get(key)
        return json.loads(value) if value else None

    async def set_user_profile(self, user_id: int, profile: dict[str, Any]) -> None:
        """
        缓存用户资料。

        :param user_id: 用户 ID
        :param profile: 用户资料
        :return: None
        """
        await self._set_profile(f"{self.USER_PROFILE_KEY_PREFIX}:{user_id}", profile)

    async def get_user_profile(self, user_id: int) -> dict[str, Any] | None:
        """
        获取用户资料缓存。

        :param user_id: 用户 ID
        :return: 用户资料
        """
        return await self._get_profile(f"{self.USER_PROFILE_KEY_PREFIX}:{user_id}")

    async def set_group_profile(self, group_id: int, profile: dict[str, Any]) -> None:
        """
        缓存群组资料。

        :param group_id: 群组 ID
        :param profile: 群组资料
        :return: None
        """
        await self._set_profile(f"{self.GROUP_PROFILE_KEY_PREFIX}:{group_id}", profile)

    async def get_group_profile(self, group_id: int) -> dict[str, Any] | None:
        """
        获取群组资料缓存。

        :param group_id: 群组 ID
        :return: 群组资料
        """
        return await self._get_profile(f"{self.GROUP_PROFILE_KEY_PREFIX}:{group_id}")

    async def publish(self, envelope: WebSocketEnvelope) -> None:
        """
        发布跨 worker WebSocket 消息。

        :param envelope: 消息信封
        :return: None
        """
        await self.get_redis().publish(self.CHANNEL, envelope.model_dump_json())
