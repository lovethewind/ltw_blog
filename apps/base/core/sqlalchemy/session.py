from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.base.core.depend_inject import Component, GetBean, RefreshScope, Value, container


@Component()
@RefreshScope("app.db.sqlalchemy")
class SqlAlchemySessionManager:
    """
    SQLAlchemy Session 管理器。
    """

    config: dict[str, Any] = Value("app.db.sqlalchemy")
    _ENGINE_OPTION_KEYS = frozenset(
        {
            "echo",
            "pool_pre_ping",
            "pool_recycle",
            "pool_size",
            "max_overflow",
            "pool_timeout",
        }
    )
    _SESSION_OPTION_KEYS = frozenset({"expire_on_commit", "autoflush", "autobegin"})

    def __init__(self) -> None:
        """
        初始化 SQLAlchemy Engine 和 Session 工厂。

        :return: None。
        """
        sqlalchemy_url, engine_options, session_options = self._build_sqlalchemy_config()
        self.engine = create_async_engine(sqlalchemy_url, **engine_options)
        self.session_factory = async_sessionmaker(self.engine, **session_options)
        self.closed = False

    def _build_sqlalchemy_config(self) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """
        构建 SQLAlchemy URL、Engine 参数和 Session 参数。

        :return: URL、Engine 参数、Session 参数。
        """
        sqlalchemy_url = self._build_sqlalchemy_url(self.config)
        engine_options = self._collect_options(self.config, self._ENGINE_OPTION_KEYS, ("engine", "engine_options"))
        session_options = self._collect_options(self.config, self._SESSION_OPTION_KEYS, ("session", "session_options"))
        engine_options.setdefault("pool_pre_ping", True)
        session_options.setdefault("expire_on_commit", False)
        return sqlalchemy_url, engine_options, session_options

    def _collect_options(
        self, config: dict[str, Any], keys: frozenset[str], nested_names: tuple[str, ...]
    ) -> dict[str, Any]:
        """
        从配置中收集指定选项。

        :param config: SQLAlchemy 数据库配置。
        :param keys: 允许收集的选项名。
        :param nested_names: 嵌套配置键名。
        :return: 过滤后的选项字典。
        :raises ValueError: 嵌套配置不是字典时抛出。
        """
        options = {key: config[key] for key in keys if key in config and config[key] is not None}
        for nested_name in nested_names:
            nested_config = config.get(nested_name) or {}
            if not isinstance(nested_config, dict):
                raise ValueError(f"SQLAlchemy 配置[{nested_name}]必须是字典")
            options.update(
                {key: nested_config[key] for key in keys if key in nested_config and nested_config[key] is not None}
            )
        return options

    def _build_sqlalchemy_url(self, config: dict[str, Any]) -> str:
        """
        从 SQLAlchemy 配置构建异步连接字符串。

        :param config: SQLAlchemy 数据库配置。
        :return: SQLAlchemy 异步连接字符串。
        :raises ValueError: 数据库连接配置缺失或格式不支持时抛出。
        """
        url = config.get("url") or config.get("database_url")
        if isinstance(url, str) and url:
            return self._normalize_connection_url(url)

        connections = config.get("connections") or {}
        connection_name = self._get_default_connection_name(config)
        connection = connections.get(connection_name)
        if not connection:
            raise ValueError(f"缺少数据库连接配置: {connection_name}")
        if isinstance(connection, str):
            return self._normalize_connection_url(connection)
        raise ValueError(f"不支持的数据库连接配置: {connection_name}")

    def _get_default_connection_name(self, config: dict[str, Any]) -> str:
        """
        获取默认数据库连接名称。

        :param config: SQLAlchemy 数据库配置。
        :return: 默认连接名称。
        """
        return config.get("apps", {}).get("models", {}).get("default_connection") or "default"

    def _normalize_connection_url(self, connection: str) -> str:
        """
        规范化连接字符串为 SQLAlchemy 异步驱动格式。

        :param connection: 原始连接字符串。
        :return: SQLAlchemy 异步连接字符串。
        """
        if connection.startswith("mysql://"):
            return connection.replace("mysql://", "mysql+asyncmy://", 1)
        if connection.startswith("mysql+aiomysql://"):
            return connection.replace("mysql+aiomysql://", "mysql+asyncmy://", 1)
        return connection

    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        获取 SQLAlchemy 异步 Session 工厂。

        :return: SQLAlchemy 异步 Session 工厂。
        """
        return self.session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        提供 SQLAlchemy 异步 Session 上下文。

        :return: SQLAlchemy 异步 Session。
        """
        async with self.session_factory() as session:
            yield session

    async def close(self) -> None:
        """
        关闭 SQLAlchemy Engine。

        :return: None。
        """
        if self.closed:
            return
        await self.engine.dispose()
        self.closed = True


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    获取全局 SQLAlchemy 异步 Session 工厂。

    :return: SQLAlchemy 异步 Session 工厂。
    """
    return GetBean(SqlAlchemySessionManager).get_session_factory()


def init_sqlalchemy_engine() -> SqlAlchemySessionManager:
    """
    初始化 SQLAlchemy Engine 和 Session 工厂。

    :return: SQLAlchemy Session 管理器。
    """
    return GetBean(SqlAlchemySessionManager)


async def close_sqlalchemy_engine() -> None:
    """
    关闭全局 SQLAlchemy 异步 Engine。

    :return: None。
    """
    manager = GetBean(SqlAlchemySessionManager)
    await manager.close()


def reset_sqlalchemy_state() -> None:
    """
    重置 SQLAlchemy 全局状态，供测试隔离使用。

    :return: None。
    """
    manager_provider = container.providers.get("sqlAlchemySessionManager")
    if manager_provider is not None:
        manager_provider.reset()


@asynccontextmanager
async def sqlalchemy_context() -> AsyncGenerator[None, None]:
    """
    提供 SQLAlchemy 生命周期上下文，脚本使用。

    :return: 异步上下文生成器。
    """
    get_session_factory()
    try:
        yield
    finally:
        await close_sqlalchemy_engine()


@asynccontextmanager
async def sqlalchemy_session() -> AsyncGenerator[AsyncSession, None]:
    """
    提供 SQLAlchemy 异步 Session 上下文。

    :return: SQLAlchemy 异步 Session。
    """
    async with GetBean(SqlAlchemySessionManager).session() as session:
        yield session
