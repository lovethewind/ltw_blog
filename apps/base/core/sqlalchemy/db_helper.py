from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Sequence, Type, TypeVar

from sqlalchemy import Result, Row, Select, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.base.core.sqlalchemy.base_model import BaseModel
from apps.base.core.sqlalchemy.session import get_session_factory

T = TypeVar("T", bound=BaseModel)


class AsyncDBHelper:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        """
        初始化异步数据库助手。

        :param session_factory: 可选 Session 工厂；为空时按需获取全局工厂。
        :return: None。
        """
        self._session_factory = session_factory

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        获取当前可用的 SQLAlchemy Session 工厂。

        :return: SQLAlchemy 异步 Session 工厂。
        """
        return self._session_factory or get_session_factory()

    def page(self, current: int, size: int) -> tuple[int, int]:
        """
        计算分页偏移量和查询数量。

        :param current: 当前页码。
        :param size: 每页数量。
        :return: offset 与 limit。
        """
        current = current if current > 0 else 1
        size = size if size > 0 else 10
        return (current - 1) * size, size

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        提供 Session 上下文管理器。

        :return: SQLAlchemy 异步 Session。
        """
        async with self.session_factory() as session:
            yield session

    @asynccontextmanager
    async def atomic(self) -> AsyncGenerator[AsyncSession, None]:
        """
        提供事务自动提交上下文。

        :return: SQLAlchemy 异步 Session。
        """
        async with self.session_factory.begin() as session:
            yield session

    async def execute(self, stmt: Any, session: AsyncSession | None = None) -> Result[Any]:
        """
        在事务中执行 SQLAlchemy 语句。

        :param stmt: SQLAlchemy 语句。
        :param session: 复用的session。
        :return: 执行结果。
        """
        if session:
            return await session.execute(stmt)
        async with self.atomic() as session:
            return await session.execute(stmt)

    async def create(self, data: T, return_value: bool = True) -> T | None:
        """
        插入单个模型对象。

        :param data: 待插入的模型对象。
        :param return_value: 是否刷新并返回插入后的模型对象。
        :return: 插入后的模型对象；不需要返回值时返回 None。
        """
        async with self.atomic() as session:
            session.add(data)
            if not return_value:
                return None
            await session.flush()
            return data

    async def create_or_update(self, model: Type[T], data: dict[str, Any], update_columns: list[str]) -> Result[Any]:
        """
        创建或更新对象
        :param model: 模型类
        :param data: 要插入的数据
        :param update_columns: 冲突后要更新的字段
        :return:
        """
        stmt = insert(model).values(**data)
        if update_columns:
            update_dict = {key: getattr(stmt.inserted, key) for key in update_columns}
            stmt = stmt.on_duplicate_key_update(**update_dict)
        else:
            stmt = stmt.prefix_with("IGNORE")
        async with self.atomic() as session:
            return await session.execute(stmt)

    async def get_or_create(
        self,
        model: Type[T],
        lookup: dict[str, Any],
        defaults: dict[str, Any] | None = None,
    ) -> tuple[T, bool]:
        """
        查询或创建模型对象。

        并发安全依赖 lookup 对应字段在数据库层存在唯一约束。

        :param model: 模型类。
        :param lookup: 查询唯一对象的等值字段条件。
        :param defaults: 创建对象时额外写入的默认字段。
        :return: 模型对象和是否新建。
        """

        defaults = defaults or {}
        create_data = {**lookup, **defaults}
        async with self.atomic() as session:
            stmt = select(model).filter_by(**lookup)
            obj = await session.scalar(stmt)
            if obj is not None:
                return obj, False

            obj = model(**create_data)
            session.add(obj)
            try:
                await session.flush()
                return obj, True
            except IntegrityError:
                await session.rollback()
                # 并发情况下，别人可能已经插入成功了，这里重新查一次
                obj = await session.scalar(stmt)
                if obj is None:
                    raise
                return obj, False

    async def all(self, stmt: Select) -> Sequence[Row]:
        """
        查询全部行结果。

        :param stmt: SQLAlchemy 查询语句。
        :return: 行列表。
        """
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.all()

    async def model_all(self, stmt: Select) -> Sequence[Any]:
        """
        查询全部模型结果。

        :param stmt: SQLAlchemy 查询语句。
        :return: 模型结果列表。
        """
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.scalars().all()

    async def first(self, stmt: Select) -> Any:
        """
        获取第一个结果行。

        :param stmt: SQLAlchemy 查询语句。
        :return: Row对象。
        """
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.first()

    async def model_first(self, stmt: Select) -> Any:
        """
        获取第一个结果实例。

        :param stmt: SQLAlchemy 查询语句。
        :return: 实例或None。
        """
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.scalars().first()

    async def scalar(self, stmt: Select) -> Any:
        """
        获取单个值。

        :param stmt: SQLAlchemy 查询语句。
        :return:
        """
        async with self.session_factory() as session:
            return await session.scalar(stmt)

    async def stream_rows(self, stmt: Select, chunk_size: int = 1000) -> AsyncGenerator[Row, None]:
        """
        流式返回Row列表。

        :param stmt: SQLAlchemy 查询语句。
        :param chunk_size: 流式大小。
        :return: Row 异步生成器。
        """
        async with self.session_factory() as session:
            result = await session.stream(stmt.execution_options(yield_per=chunk_size))

            async for row in result:
                yield row

    async def stream_scalars(self, stmt: Select, chunk_size: int = 1000) -> AsyncGenerator[Any, None]:
        """
        流式返回模型对象列表。

        :param stmt: SQLAlchemy 查询语句。
        :param chunk_size: 流式大小。
        :return: 模型对象异步生成器。
        """
        async with self.session_factory() as session:
            result = await session.stream_scalars(stmt.execution_options(yield_per=chunk_size))

            async for item in result:
                yield item


db = AsyncDBHelper()
