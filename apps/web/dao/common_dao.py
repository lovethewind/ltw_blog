# @Time    : 2024/8/28 13:42
# @Author  : frank
# @File    : common_dao.py
from typing import Type, TypeVar

from tortoise import Tortoise

from apps.base.core.depend_inject import Component, Value
from apps.web.dto.base_dto import BaseDTO

T = TypeVar("T", bound=BaseDTO)


@Component()
class CommonDao:
    default_connection: str = Value("app.db.tortoise.apps.models.default_connection")

    def __init__(self):
        self.db = Tortoise.get_connection(self.default_connection)

    async def execute_sql(self, sql: str, params: list | tuple = None):
        return await self.db.execute_query_dict(sql, params)

    async def execute_sql_dto(self, sql: str, params: list | tuple = None, clazz: Type[T] = None) -> list[T]:
        ret = await self.db.execute_query_dict(sql, params)
        return clazz.bulk_model_validate(ret)
