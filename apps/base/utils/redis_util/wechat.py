import datetime

from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant


class WechatMethod:
    """
    wechat操作
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def save_wechat_code_openid(self, code: str, openid: str) :
        """
        保存微信临时码-openId
        """
        key = f"{RedisConstant.WECHAT_CODE_OPENID_KEY}:{code}"
        await self._redis.set(key, openid, ex=datetime.timedelta(days=1))

    async def get_wechat_code_openid(self, code: str) -> str:
        """
        获取微信临时码-openId
        """
        key = f"{RedisConstant.WECHAT_CODE_OPENID_KEY}:{code}"
        ret = await self._redis.get(key)
        return ret

    async def delete_wechat_code_openid(self, code: str):
        """
        删除微信临时码-openId
        """
        key = f"{RedisConstant.WECHAT_CODE_OPENID_KEY}:{code}"
        await self._redis.delete(key)

    async def save_random_code_openid(self, code: str, openid: str,
                                      ex: int | datetime.timedelta = datetime.timedelta(minutes=1)) :
        """
        保存随机验证码及openId
        """
        key = f"{RedisConstant.RANDOM_CODE_OPENID_KEY}:{code}"
        await self._redis.set(key, openid, ex=ex)

    async def exist_random_code_openid(self, code: str) -> bool:
        """
        是否存在该随机验证码
        """
        return await self._redis.exists(f"{RedisConstant.RANDOM_CODE_OPENID_KEY}:{code}")

    async def get_random_code_openid(self, code: str) -> str:
        """
        获取临时码对应的openId
        """
        key = f"{RedisConstant.RANDOM_CODE_OPENID_KEY}:{code}"
        ret = await self._redis.get(key)
        return ret

    async def delete_random_code_openid(self, code: str) :
        """
        删除随机验证码
        """
        key = f"{RedisConstant.RANDOM_CODE_OPENID_KEY}:{code}"
        await self._redis.delete(key)
