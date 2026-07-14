import importlib
import inspect
from collections.abc import Callable
from typing import Any

ALLOWED_TARGET_PREFIX = "apps.scheduler.tasks."


def resolve_invoke_target(target: str) -> Callable[..., Any]:
    """解析允许执行的定时任务调用目标。

    :param target: 点分隔的模块函数路径
    :return: 可调用函数
    :raises ValueError: 调用目标格式错误、越过白名单或指向私有符号时抛出
    """
    module_name, separator, function_name = target.rpartition(".")
    if not separator or not module_name or not function_name:
        raise ValueError("定时任务调用目标格式无效")
    if not module_name.startswith(ALLOWED_TARGET_PREFIX):
        raise ValueError(f"不允许执行调用目标：{target}")
    if function_name.startswith("_"):
        raise ValueError("定时任务不能调用私有符号")
    module = importlib.import_module(module_name)
    function = getattr(module, function_name, None)
    if not callable(function) or inspect.isclass(function):
        raise ValueError(f"定时任务调用目标不是函数：{target}")
    return function


async def invoke_target(target: str) -> Any:
    """执行定时任务调用目标并兼容同步与异步函数。

    :param target: 点分隔的模块函数路径
    :return: 函数执行结果
    """
    result = resolve_invoke_target(target)()
    if inspect.isawaitable(result):
        return await result
    return result
