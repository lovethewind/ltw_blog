import asyncio
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.asyncio.lock import Lock
from redis.exceptions import LockNotOwnedError

from apps.base.core.depend_inject import Value, Component, RefreshScope, logger
from .article import ArticleMethod
from .chat import ChatMethod
from .comment import CommentMethod
from .es import ESMethod
from .acrion import ActionMethod
from .picture import PictureMethod
from .share import ShareMethod
from .user import UserMethod
from .verify_code import VerifyCodeMethod
from .website import WebsiteMethod
from .wechat import WechatMethod


@Component()
@RefreshScope("redis")
class RedisUtil:
    config: dict = Value("redis")

    def __init__(self):
        pool = redis.ConnectionPool(decode_responses=True, **self.config)
        self.redis = redis.Redis(connection_pool=pool)
        self.Article = ArticleMethod(self.redis)
        self.Action = ActionMethod(self.redis)
        self.VerifyCode = VerifyCodeMethod(self.redis)
        self.User = UserMethod(self.redis)
        self.Wechat = WechatMethod(self.redis)
        self.Comment = CommentMethod(self.redis)
        self.Website = WebsiteMethod(self.redis)
        self.ES = ESMethod(self.redis)
        self.Share = ShareMethod(self.redis)
        self.Picture = PictureMethod(self.redis)
        self.Chat = ChatMethod(self.redis)

    async def get(self, key: str):
        return await self.redis.get(key)

    async def set(self, key: str, value: Any, *args, **kwargs):
        return await self.redis.set(key, value, *args, **kwargs)

    async def delete(self, key: str):
        return await self.redis.delete(key)

    def get_lock(self,
                 name: str,
                 timeout: int = 60,
                 sleep: float = 0.1,
                 blocking: bool = False,
                 blocking_timeout: int = 3,
                 renew=True):
        return AsyncAutoRenewLock(self.redis, name, timeout, sleep, blocking, blocking_timeout, renew)


class AsyncAutoRenewLock(Lock):
    def __init__(self, _redis: Redis,
                 name: str,
                 timeout: int = 60,
                 sleep: float = 0.1,
                 blocking: bool = False,
                 blocking_timeout: int = 30,
                 renew: bool = True):
        self.renew = renew
        self.renew_ttl = round(timeout / 3, 2)
        self.renew_task: Optional[asyncio.Task] = None
        super().__init__(_redis, name, timeout, sleep, blocking, blocking_timeout)

    async def acquire(self,
                      blocking: Optional[bool] = None,
                      blocking_timeout: Optional[float] = None,
                      token: Optional[str | bytes] = None, ) -> bool:
        """
        异步尝试获取锁。
        """
        acquired = await super().acquire(blocking, blocking_timeout, token)
        if not acquired:
            return False
        if self.renew:
            # 启动一个任务来自动续期锁
            self.renew_task = asyncio.create_task(self._renew_lock())
        return True

    async def _renew_lock(self):
        """
        异步任务，用于自动续期锁。
        """
        while True:
            if await self.locked():
                await asyncio.sleep(self.renew_ttl)
                await self.extend(self.timeout)
                logger.info(f"Lock {self.name} renewed.")
                continue
            return

    async def release(self):
        """
        释放锁并取消续期任务。
        """
        try:
            await super().release()
        except LockNotOwnedError:
            pass
        if self.renew_task:
            self.renew_task.cancel()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()
