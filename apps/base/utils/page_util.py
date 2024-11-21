# @Time    : 2024/9/25 00:02
# @Author  : frank
# @File    : page_util.py
import asyncio
import math
from typing import Any

from tortoise import Tortoise
from tortoise.queryset import QuerySet

from apps.base.core.depend_inject import GetValue
from apps.web.dto.base_dto import BaseDTO


class PageResult[T](BaseDTO):
    total: int
    current: int
    size: int
    pages: int
    records: list[T]
    main_total: int = 0

    def __init__(self, /, records: list[T], **data: Any):
        data.update(records=records, pages=math.ceil(data.get("total", 0) / data.get("size", 1)))
        super().__init__(**data)


class Pagination[T]:

    def __init__(self,
                 current_page: int,
                 page_size: int,
                 q: QuerySet[T] = None,
                 *,
                 q_count: QuerySet[T] = None,
                 sql: str = None,
                 sql_args: list = None,
                 select_columns="*"):
        self.current_page = current_page
        self.page_size = page_size
        self.q = q_count or q
        self.sql = sql
        self.sql_args = sql_args
        self.select_columns = select_columns
        self.db = Tortoise.get_connection(GetValue("app.db.tortoise.apps.models.default_connection"))

    async def execute(self):
        self.current_page = self.current_page if self.current_page > 0 else 1
        self.page_size = self.page_size if self.page_size > 0 else 10
        if self.q:
            count, records = await self._execute_queryset()
        else:
            count, records = await self._execute_sql()
        generic_type = getattr(self, "__orig_class__").__args__[0]
        if issubclass(generic_type, BaseDTO):
            records: list[T] = generic_type.bulk_model_validate(records)
        return PageResult(
            total=count,
            current=self.current_page,
            size=self.page_size,
            records=records,
        )

    async def _execute_queryset(self):
        q_count = self.q.count()
        q_records = self.q.offset((self.current_page - 1) * self.page_size).limit(self.page_size).all()
        count, records = await asyncio.gather(
            q_count,
            q_records
        )
        return count, records

    async def _execute_sql(self):
        q_count = self.sql.format(select_columns="count(*) as count")
        q_records = self.sql.format(select_columns=self.select_columns)
        count, records = await asyncio.gather(
            self.db.execute_query_dict(q_count, self.sql_args),
            self.db.execute_query_dict(q_records, self.sql_args)
        )
        count = count[0]["count"] if count else 0
        return count, records
