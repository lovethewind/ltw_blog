from sqlalchemy import func, select

from apps.base.constant.redis_constant import RedisConstant
from apps.base.core.depend_inject import Component, RefreshScope, logger
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.user import User
from apps.base.utils.redis_util import RedisUtil as BaseRedisUtil


class AdminUserRedisMethod:
    """
    后台用户 Redis 方法。
    """

    def __init__(self, redis) -> None:
        """
        初始化后台用户 Redis 方法。

        :param redis: Redis 客户端。
        :return: None。
        """
        self._redis = redis

    async def gen_uid(self) -> int:
        """
        生成用户 UID。

        :return: 用户 UID。
        """
        key = RedisConstant.USER_UID_GENERATOR_KEY
        if not await self._redis.exists("uid"):
            stmt = select(func.max(User.uid))
            value = await db.scalar(stmt) or 0
            value = max(value, 10000)
            logger.info(f"init uid cache:{value}")
            await self._redis.set(key, value)
        return await self._redis.incr(key)

    async def delete_user_profile_cache(self, user_id: int) -> None:
        """
        删除指定用户的资料缓存。

        :param user_id: 用户 ID。
        :return: None。
        """
        key = f"{RedisConstant.USER_PROFILE_CACHE_KEY_PREFIX}:{user_id}"
        await self._redis.delete(key)


@Component("adminRedisUtil")
@RefreshScope("redis")
class AdminRedisUtil(BaseRedisUtil):
    """
    后台 Redis 聚合工具。
    """

    def __init__(self) -> None:
        """
        初始化后台 Redis 方法。

        :return: None。
        """
        super().__init__()
        self.User: AdminUserRedisMethod = AdminUserRedisMethod(self.redis)
