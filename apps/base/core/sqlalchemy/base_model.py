from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Select, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from apps.base.utils.snowflake import SnowflakeIDGenerator


class BaseModel(DeclarativeBase):
    """
    SQLAlchemy 声明式模型基类。
    """

    id: Mapped[int] = mapped_column(
        BigInteger, default=SnowflakeIDGenerator.generate_id, primary_key=True, comment="主键"
    )
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    @classmethod
    def select(cls, *columns: Any) -> Select:
        """
        构建当前模型的查询语句。

        :param columns: 可选查询字段；为空时查询当前模型。
        :return: SQLAlchemy 查询语句。
        """
        return select(*(columns or (cls,)))
