from contextlib import asynccontextmanager
from copy import deepcopy
from typing import Any, AsyncGenerator, Callable

from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from apps.base.core.depend_inject import GetValue

DEFAULT_TIMEZONE = "Asia/Shanghai"


def _init_default_config() -> None:
    """
    初始化默认 Web 配置容器。

    :return: None。
    """
    from apps.web.config.server_config import init_container_config

    init_container_config()


def build_tortoise_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    构建 Tortoise 配置副本，并补齐项目默认时区策略。

    :param config: 原始 Tortoise 配置。
    :return: 补齐默认值后的配置副本。
    """
    tortoise_config = deepcopy(config)
    tortoise_config.setdefault("use_tz", False)
    tortoise_config.setdefault("timezone", DEFAULT_TIMEZONE)
    return tortoise_config


def register_app_tortoise(
    app: FastAPI,
    tortoise_config: dict[str, Any],
    testing_config: dict[str, Any],
    testing: bool = False,
) -> None:
    """
    为 FastAPI 应用注册 Tortoise。

    :param app: FastAPI 应用。
    :param tortoise_config: 正常运行数据库配置。
    :param testing_config: 测试数据库配置。
    :param testing: 是否使用测试数据库配置。
    :return: None。
    """
    config = build_tortoise_config(testing_config if testing else tortoise_config)
    register_tortoise(app, config)


async def init_tortoise(
    init_config: Callable[[], None] | None = None,
    config: dict[str, Any] | None = None,
) -> None:
    """
    初始化脚本场景下使用的 Tortoise。

    :param init_config: 配置容器初始化函数；为空且未指定 config 时默认初始化 Web 配置。
    :param config: 指定 Tortoise 配置；为空时从配置容器读取。
    :return: None。
    """
    if init_config:
        init_config()
    elif config is None:
        _init_default_config()
    tortoise_config = config or GetValue("app.db.tortoise")
    await Tortoise.init(config=build_tortoise_config(tortoise_config))


@asynccontextmanager
async def tortoise_context(
    init_config: Callable[[], None] | None = None,
    config: dict[str, Any] | None = None,
) -> AsyncGenerator[None, None]:
    """
    提供脚本使用的 Tortoise 生命周期上下文。

    :param init_config: 配置容器初始化函数；为空且未指定 config 时默认初始化 Web 配置。
    :param config: 指定 Tortoise 配置；为空时从配置容器读取。
    :return: 异步上下文生成器。
    """
    await init_tortoise(init_config=init_config, config=config)
    try:
        yield
    finally:
        await Tortoise.close_connections()
