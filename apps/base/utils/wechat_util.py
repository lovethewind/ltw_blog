import base64
import json

import aiohttp

from apps.base.core.depend_inject import Component, Value, Autowired, logger
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.utils.redis_util import RedisUtil
from apps.base.utils.snowflake import SnowflakeIDGenerator


@Component()
class WechatUtil:
    app_id: str = Value("wx.app-id")
    app_secret: str = Value("wx.app-secret")
    env_version: str = Value("wx.env-version")
    page: str = Value("wx.page")
    redis_util: RedisUtil = Autowired()
    TYPE_AUTHORIZATION_CODE = "authorization_code"
    TYPE_CLIENT_CREDENTIAL = "client_credential"
    GET_OPEN_ID_URL = "https://api.weixin.qq.com/sns/jscode2session"
    GET_ACCESS_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
    GET_UNION_ID_URL = "https://api.weixin.qq.com/cgi-bin/user/info"
    GET_WXA_CODE_URL = "https://api.weixin.qq.com/wxa/getwxacodeunlimit"
    GET_USER_INFO_URL = "https://api.weixin.qq.com/sns/userinfo"
    ACCESS_TOKEN_KEY = "wechat_access_token"
    ACCESS_TOKEN_LOCK_KEY = "wechat_access_token_lock"

    def _get_base_url(self, url: str, grant_type: str) -> str:
        return f"{url}?appid={self.app_id}&secret={self.app_secret}&grant_type={grant_type}"

    def get_random_code(self, code_type: int) -> str:
        return f"{SnowflakeIDGenerator.generate_id()}{code_type}"

    async def get_open_id(self, code: str) -> str | None:
        """
        获取openId
        :param code: code
        :return: openId
        """
        if not code:
            return
        url = self._get_base_url(self.GET_OPEN_ID_URL, self.TYPE_AUTHORIZATION_CODE) + f"&js_code={code}"
        async with aiohttp.ClientSession() as session:
            response = await session.get(url)
            ret: str = await response.text()
            ret: dict = json.loads(ret)
            logger.info(f"url:{url} | response:{ret}")
            if ret.get("errcode"):
                logger.info(f"获取openId出错: {ret}")
                return
            return ret.get("openid")

    async def get_access_token(self) -> str:
        access_token = await self.redis_util.get(self.ACCESS_TOKEN_KEY)
        if access_token:
            return access_token
        lock = self.redis_util.get_lock(self.ACCESS_TOKEN_LOCK_KEY, blocking=True)
        async with lock:
            access_token = await self.redis_util.get(self.ACCESS_TOKEN_KEY)
            if access_token:
                return access_token
            url = self._get_base_url(self.GET_ACCESS_TOKEN_URL, self.TYPE_CLIENT_CREDENTIAL)
            async with aiohttp.ClientSession() as session:
                try:
                    response = await session.get(url)
                    ret: dict = await response.json()
                    logger.info(f"url:{url} | response:{ret}")
                    access_token: str = ret.get("access_token")
                    if not access_token:
                        raise MyException()
                    await self.redis_util.set(self.ACCESS_TOKEN_KEY, access_token, ex=2 * 60 * 60)
                    return access_token
                except Exception as e:
                    logger.error(f"获取access_token出错: {e}")
                    raise e

    async def get_applet_code(self, scene: str) -> str:
        access_token = await self.get_access_token()
        url = f"{self.GET_WXA_CODE_URL}?access_token={access_token}"
        data = {
            "scene": scene,
            "page": self.page,
            "env_version": self.env_version,
            "check_path": self.env_version != "develop"
        }
        async with aiohttp.ClientSession() as session:
            response = await session.post(url, json=data)
            ret: bytes = await response.read()
            logger.info(f"url:{url} | body: {data} | response:{ret[:100]}")
            if ret.find(b"errcode") > -1:
                await self.refresh_access_token()
                logger.info(f"accessToken过期，重新获取, {ret}")
                access_token = await self.get_access_token()
                url = f"{self.GET_WXA_CODE_URL}?access_token={access_token}"
                response = await session.post(url, json=data)
                ret: bytes = await response.read()
                if ret.find(b"errcode"):
                    raise RuntimeError(f"刷新access_token出错: {ret.decode()}")
            return base64.b64encode(ret).decode()

    async def refresh_access_token(self):
        await self.redis_util.delete(self.ACCESS_TOKEN_KEY)
        await self.get_access_token()
