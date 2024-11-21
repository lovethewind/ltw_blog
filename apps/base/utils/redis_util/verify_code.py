import datetime

from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant
from apps.base.enum.common import VerifyCodeTypeEnum
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException


class VerifyCodeMethod:
    """
    验证码操作
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def check_verify_code(self, account: str, code: str, code_type: VerifyCodeTypeEnum) -> bool:
        """
         校验验证码
         :param account email或者手机号
         :param code    6位数验证码
         :param code_type    类型 register、find、bind、login、password
         :return bool
        """
        if not account or not code:
            return False
        key = f"{RedisConstant.VERIFY_CODE_OP_KEY}:{account}:{code_type}"
        save_code = await self._redis.get(key)
        if not save_code:
            return False
        if await self._get_account_error_times(account, code_type) >= 10:
            # 验证码1分钟之内只能验证最多10次，超过需重新获取
            await self._del_account_error_times(account, code_type)
            raise MyException(ErrorCode.CODE_VERIFY_OVER_MAX_LIMIT)
        if code != save_code:
            await self._incr_account_error_times(account, code_type)
            return False
        return True

    async def _get_account_error_times(self, account: str, code_type: VerifyCodeTypeEnum) -> int:
        """
        获取验证码错误次数
        :param account: email或者手机号
        :param code_type: 类型 register、find、bind
        :return:
        """
        error_count_key = f"{RedisConstant.VERIFY_CODE_OP_KEY}:error:{account}:{code_type}"
        count = await self._redis.get(error_count_key) or 0
        return int(count)

    async def _incr_account_error_times(self, account: str, code_type: VerifyCodeTypeEnum):
        """
        增加验证码错误次数
        :param account: email或者手机号
        :param code_type: 类型 register、find、bind
        :return:
        """
        error_count_key = f"{RedisConstant.VERIFY_CODE_OP_KEY}:error:{account}:{code_type}"
        if not await self._redis.exists(error_count_key):
            await self._redis.set(error_count_key, 0, ex=datetime.timedelta(minutes=1))
        await self._redis.incr(error_count_key)

    async def _del_account_error_times(self, account: str, code_type: VerifyCodeTypeEnum):
        """
        删除验证码错误次数
        :param account: email或者手机号
        :param code_type: 类型 register、find、bind
        :return:
        """
        error_count_key = f"{RedisConstant.VERIFY_CODE_OP_KEY}:error:{account}:{code_type}"
        code_key = f"{RedisConstant.VERIFY_CODE_OP_KEY}:{account}:{code_type}"
        await self._redis.delete(code_key, error_count_key)

    async def delete_verify_code(self, account: str, code_type: VerifyCodeTypeEnum):
        """
        删除验证码
        :param account: email或者手机号
        :param code_type: 类型 register、find、bind、login、password
        :return:
        """
        error_count_key = f"{RedisConstant.VERIFY_CODE_OP_KEY}:error:{account}:{code_type}"
        code_key = f"{RedisConstant.VERIFY_CODE_OP_KEY}:{account}:{code_type}"
        await self._redis.delete(code_key, error_count_key)

    async def save_verify_code(self, account: str, code: str, code_type: VerifyCodeTypeEnum):
        """
        保存验证码
        :param account: email或者手机号
        :param code: 6位数验证码
        :param code_type: 类型 register、find、bind
        :return:
        """
        if not account or not code:
            return
        key = f"{RedisConstant.VERIFY_CODE_OP_KEY}:{account}:{code_type}"
        await self._redis.set(key, code, ex=datetime.timedelta(minutes=15))
