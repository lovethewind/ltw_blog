# @Time    : 2024/9/14 14:22
# @Author  : frank
# @File    : website.py

import datetime

from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant


class WebsiteMethod:
    """
    website操作
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def incr_website_view_count(self, ip_address: str,
                                  throttle_rate: int | datetime.timedelta = datetime.timedelta(minutes=1)):
        """
        增加网站访问量
        """
        throttle_key = f"{RedisConstant.WEBSITE_VIEW_COUNT_THROTTLE_KEY}:{ip_address}"
        if not await self._redis.set(throttle_key, 1, ex=throttle_rate, nx=True):
            return
        await self._redis.incr(RedisConstant.WEBSITE_VIEW_COUNT_KEY)

    async def get_website_view_count(self) -> int:
        """
        获取网站访问量
        """
        ret = await self._redis.get(RedisConstant.WEBSITE_VIEW_COUNT_KEY) or 0
        return ret

