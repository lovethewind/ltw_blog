import datetime
import json
from dataclasses import dataclass
from enum import IntEnum

from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant


@dataclass(slots=True)
class WechatScanContext:
    """微信扫码上下文。"""

    code_type: int
    user_id: int | None
    open_id: str = ""
    scanned: bool = False


class WechatScanUpdateResult(IntEnum):
    """微信扫码上下文更新结果。"""

    EXPIRED = -1
    CONFLICT = 0
    SUCCESS = 1


class WechatMethod:
    """
    wechat操作
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def save_wechat_code_openid(self, code: str, openid: str):
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

    async def save_random_code_openid(
        self,
        code: str,
        openid: str,
        code_type: int,
        user_id: int | None,
        ex: int | datetime.timedelta = datetime.timedelta(minutes=5),
    ) -> None:
        """
        保存微信扫码上下文。

        :param code: 二维码随机码。
        :param openid: 微信 OpenID。
        :param code_type: 二维码用途类型。
        :param user_id: 发起扫码流程的用户 ID，匿名流程为空。
        :param ex: 有效期。
        :return: None。
        """
        key = f"{RedisConstant.RANDOM_CODE_OPENID_KEY}:{code}"
        context = WechatScanContext(code_type=code_type, user_id=user_id, open_id=openid)
        data = {
            "code_type": context.code_type,
            "user_id": str(context.user_id) if context.user_id is not None else None,
            "open_id": context.open_id,
            "scanned": context.scanned,
        }
        await self._redis.set(key, json.dumps(data), ex=ex)

    async def mark_random_code_scanned(
        self,
        code: str,
        ex: int | datetime.timedelta = datetime.timedelta(minutes=5),
    ) -> bool:
        """
        原子标记二维码已被微信扫描，但尚未确认。

        :param code: 二维码随机码。
        :param ex: 标记扫码后的有效期。
        :return: 是否成功标记。
        """
        key = f"{RedisConstant.RANDOM_CODE_OPENID_KEY}:{code}"
        seconds = int(ex.total_seconds()) if isinstance(ex, datetime.timedelta) else ex
        script = """
        local raw = redis.call('GET', KEYS[1])
        if not raw then
            return 0
        end
        local context = cjson.decode(raw)
        context['scanned'] = true
        redis.call('SET', KEYS[1], cjson.encode(context), 'EX', ARGV[1])
        return 1
        """
        result = await self._redis.eval(script, 1, key, seconds)
        return bool(result)

    async def update_random_code_openid(
        self, code: str, openid: str, ex: int | datetime.timedelta = datetime.timedelta(minutes=10)
    ) -> WechatScanUpdateResult:
        """
        原子写入扫码 OpenID，防止同一二维码被不同微信覆盖。

        :param code: 二维码随机码。
        :param openid: 微信 OpenID。
        :param ex: 更新后的有效期。
        :return: 更新结果。
        """
        key = f"{RedisConstant.RANDOM_CODE_OPENID_KEY}:{code}"
        seconds = int(ex.total_seconds()) if isinstance(ex, datetime.timedelta) else ex
        script = """
        local raw = redis.call('GET', KEYS[1])
        if not raw then
            return -1
        end
        local context = cjson.decode(raw)
        local current_openid = context['open_id'] or ''
        if current_openid ~= '' then
            if current_openid == ARGV[1] then
                return 1
            end
            return 0
        end
        context['open_id'] = ARGV[1]
        redis.call('SET', KEYS[1], cjson.encode(context), 'EX', ARGV[2])
        return 1
        """
        result = await self._redis.eval(script, 1, key, openid, seconds)
        return WechatScanUpdateResult(result)

    async def get_random_code_context(self, code: str | None) -> WechatScanContext | None:
        """
        获取微信扫码上下文。

        :param code: 二维码随机码。
        :return: 扫码上下文，不存在或旧格式数据时返回 None。
        """
        if not code:
            return None
        key = f"{RedisConstant.RANDOM_CODE_OPENID_KEY}:{code}"
        raw = await self._redis.get(key)
        if not raw:
            return None
        try:
            data = json.loads(raw)
            return WechatScanContext(
                code_type=int(data["code_type"]),
                user_id=int(data["user_id"]) if data.get("user_id") is not None else None,
                open_id=str(data.get("open_id", "")),
                scanned=bool(data.get("scanned", False)),
            )
        except KeyError, TypeError, ValueError, json.JSONDecodeError:
            return None

    async def exist_random_code_openid(self, code: str) -> bool:
        """
        判断微信扫码上下文是否有效。

        :param code: 二维码随机码。
        :return: 是否存在有效上下文。
        """
        return await self.get_random_code_context(code) is not None

    async def get_random_code_openid(self, code: str | None) -> str:
        """
        获取二维码对应的 OpenID。

        :param code: 二维码随机码。
        :return: OpenID，不存在时返回空字符串。
        """
        context = await self.get_random_code_context(code)
        return context.open_id if context else ""

    async def delete_random_code_openid(self, code: str) -> None:
        """
        删除微信扫码上下文。

        :param code: 二维码随机码。
        :return: None。
        """
        key = f"{RedisConstant.RANDOM_CODE_OPENID_KEY}:{code}"
        await self._redis.delete(key)
