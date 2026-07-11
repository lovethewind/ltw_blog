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
        self._inited = False

    async def init(self) -> None:
        """
        初始化用户 UID 生成器。

        :return: None。
        """
        key = RedisConstant.USER_UID_GENERATOR_KEY
        ret = await self._redis.get(key)
        if not ret:
            stmt = select(func.max(User.uid))
            value = await db.scalar(stmt) or 0
            value = max(value, 10000)
            logger.info(f"init uid cache:{value}")
            await self._redis.set(key, value)
        self._inited = True

    async def gen_uid(self) -> int:
        """
        生成用户 UID。

        :return: 用户 UID。
        """
        if not self._inited:
            await self.init()
        key = RedisConstant.USER_UID_GENERATOR_KEY
        return await self._redis.incr(key)


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
