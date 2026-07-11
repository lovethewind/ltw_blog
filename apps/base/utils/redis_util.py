import asyncio
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.asyncio.lock import Lock
from redis.exceptions import LockNotOwnedError

from apps.base.core.depend_inject import Value, logger


class RedisUtil:
    """
    公共 Redis 客户端工具。
    """

    config: dict = Value("redis")

    def __init__(self) -> None:
        """
        初始化 Redis 连接。

        :return: None。
        """
        pool = redis.ConnectionPool(decode_responses=True, **self.config)
        self.redis = redis.Redis(connection_pool=pool)

    async def get(self, key: str) -> Any:
        """
        获取 Redis 字符串值。

        :param key: Redis key。
        :return: Redis 值。
        """
        return await self.redis.get(key)

    async def set(self, key: str, value: Any, *args: Any, **kwargs: Any) -> Any:
        """
        设置 Redis 值。

        :param key: Redis key。
        :param value: Redis 值。
        :param args: Redis set 位置参数。
        :param kwargs: Redis set 关键字参数。
        :return: Redis set 返回值。
        """
        return await self.redis.set(key, value, *args, **kwargs)

    async def delete(self, key: str) -> Any:
        """
        删除 Redis key。

        :param key: Redis key。
        :return: Redis delete 返回值。
        """
        return await self.redis.delete(key)

    def get_lock(
        self,
        name: str,
        timeout: int = 60,
        sleep: float = 0.1,
        blocking: bool = False,
        blocking_timeout: int = 3,
        renew: bool = True,
    ) -> "AsyncAutoRenewLock":
        """
        获取自动续期分布式锁。

        :param name: 锁名称。
        :param timeout: 锁超时时间。
        :param sleep: 阻塞等待间隔。
        :param blocking: 是否阻塞等待。
        :param blocking_timeout: 阻塞等待超时时间。
        :param renew: 是否自动续期。
        :return: 自动续期锁。
        """
        return AsyncAutoRenewLock(self.redis, name, timeout, sleep, blocking, blocking_timeout, renew)


class AsyncAutoRenewLock(Lock):
    def __init__(
        self,
        _redis: Redis,
        name: str,
        timeout: int = 60,
        sleep: float = 0.1,
        blocking: bool = False,
        blocking_timeout: int = 30,
        renew: bool = True,
    ) -> None:
        """
        初始化自动续期锁。

        :param _redis: Redis 客户端。
        :param name: 锁名称。
        :param timeout: 锁超时时间。
        :param sleep: 阻塞等待间隔。
        :param blocking: 是否阻塞等待。
        :param blocking_timeout: 阻塞等待超时时间。
        :param renew: 是否自动续期。
        :return: None。
        """
        self.renew = renew
        self.renew_ttl = round(timeout / 3, 2)
        self.renew_task: Optional[asyncio.Task] = None
        super().__init__(_redis, name, timeout, sleep, blocking, blocking_timeout)

    async def acquire(
        self,
        blocking: Optional[bool] = None,
        blocking_timeout: Optional[float] = None,
        token: Optional[str | bytes] = None,
    ) -> bool:
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

    async def _renew_lock(self) -> None:
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

    async def release(self) -> None:
        """
        释放锁并取消续期任务。
        """
        try:
            await super().release()
        except LockNotOwnedError:
            pass
        if self.renew_task:
            self.renew_task.cancel()

    async def __aenter__(self) -> "AsyncAutoRenewLock":
        """
        进入异步锁上下文。

        :return: 当前锁实例。
        """
        await self.acquire()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        退出异步锁上下文。

        :param exc_type: 异常类型。
        :param exc_val: 异常值。
        :param exc_tb: 异常堆栈。
        :return: None。
        """
        await self.release()
