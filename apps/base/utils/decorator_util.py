# @Time    : 2024/9/24 23:57
# @Author  : frank
# @File    : decorator_util.py
import asyncio
from functools import wraps

from apps.base.constant.redis_constant import RedisConstant
from apps.base.core.depend_inject import ContainerUtil
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.utils.redis_util import RedisUtil
from apps.base.utils.response_util import ResponseUtil
from apps.web.config.logger_config import logger
from apps.web.vo.base_vo import BaseVO


def avoid_repeat_submit(description: str = "", renew=False, timeout=3, not_err=False, complete_release=True):
    """
    请求防重复提交
    :param renew:
    :param description:
    :param timeout:
    :param not_err:
    :param complete_release:
    :return:
    """

    def wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            biz_key = None
            for v in kwargs.values():
                if isinstance(v, BaseVO):
                    biz_key = v.biz_key
                    break
            if biz_key is None:
                logger.warn(f"{func.__name__} not found biz_key")
            redis_util = ContainerUtil.autowired(RedisUtil)
            key = f"{RedisConstant.AVOID_REPEAT_SUBMIT_KEY}:{func.__name__}:{biz_key}"
            lock = redis_util.get_lock(key, timeout=timeout, renew=renew)
            if not await lock.acquire():
                if not_err:
                    return ResponseUtil.success()
                raise MyException(ErrorCode.REPEAT_SUBMIT, data=description)
            try:
                return await func(*args, **kwargs)
            finally:
                if complete_release:
                    asyncio.create_task(lock.release())

        return inner

    return wrapper
