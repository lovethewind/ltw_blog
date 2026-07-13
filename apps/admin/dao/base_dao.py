from typing import Any, TypeVar

from sqlalchemy import Select, delete, func, select, update

from apps.base.core.sqlalchemy.base_model import BaseModel
from apps.base.core.sqlalchemy.db_helper import db

T = TypeVar("T", bound=BaseModel)


async def _paginate(stmt: Select[tuple[T]], current: int, size: int, *order_by: Any) -> tuple[list[T], int]:
    """
    执行后台列表分页查询。

    :param stmt: 查询语句。
    :param current: 当前页码。
    :param size: 每页条数。
    :param order_by: 排序字段。
    :return: 数据列表和总数。
    """
    offset, limit = db.page(current, size)
    total = await db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    records = await db.model_all(stmt.order_by(*order_by).offset(offset).limit(limit))
    return list(records), int(total or 0)


async def _create(model: type[T], data: dict[str, Any]) -> T:
    """
    创建后台管理模型。

    :param model: 模型类。
    :param data: 创建数据。
    :return: 创建后的模型对象。
    """
    item = model(**data)
    async with db.atomic() as session:
        session.add(item)
        await session.flush()
        await session.refresh(item)
    return item


async def _update(item: T, data: dict[str, Any]) -> T:
    """
    更新后台管理模型。

    :param item: 模型对象。
    :param data: 更新数据。
    :return: 更新后的模型对象。
    """
    if not data:
        return item
    for key, value in data.items():
        setattr(item, key, value)
    await db.execute(update(type(item)).where(type(item).id == item.id).values(**data))
    return item


async def _delete(model: type[T], item_id: int) -> None:
    """
    根据主键删除后台管理模型。

    :param model: 模型类。
    :param item_id: 主键 ID。
    :return: None。
    """
    await db.execute(delete(model).where(model.id == item_id))
