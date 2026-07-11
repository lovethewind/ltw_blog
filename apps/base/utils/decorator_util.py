# @Time    : 2024/9/24 23:57
# @Author  : frank
# @File    : decorator_util.py
import asyncio
import logging
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar, cast

from apps.base.constant.redis_constant import RedisConstant
from apps.base.core.depend_inject import ContainerUtil
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.utils.redis_util import RedisUtil
from apps.base.utils.response_util import ResponseUtil

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def avoid_repeat_submit(
    description: str = "",
    renew: bool = False,
    timeout: int = 3,
    not_err: bool = False,
    complete_release: bool = True,
) -> Callable[[F], F]:
    """
    请求防重复提交
    :param renew:
    :param description:
    :param timeout:
    :param not_err:
    :param complete_release:
    :return:
    """

    def wrapper(func: F) -> F:
        """
        包装接口方法并添加防重复提交逻辑。

        :param func: 被包装的异步接口方法。
        :return: 包装后的异步接口方法。
        """

        @wraps(func)
        async def inner(*args: Any, **kwargs: Any) -> Any:
            """
            执行防重复提交校验后调用原始方法。

            :param args: 原始方法位置参数。
            :param kwargs: 原始方法关键字参数。
            :return: 原始方法执行结果。
            """
            biz_key = None
            for v in kwargs.values():
                biz_key_value = getattr(v, "biz_key", None)
                if biz_key_value is not None:
                    biz_key = biz_key_value
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

        return cast(F, inner)

    return wrapper
