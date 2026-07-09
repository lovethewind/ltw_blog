from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.core.sqlalchemy.base_model import BaseModel


class Source(BaseModel):
    """
    定期删除已不再使用的资源。
    """

    __tablename__ = "t_source"
    __table_args__ = {"comment": "资源表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    url: Mapped[str] = mapped_column(String(256), comment="url")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已删除(实现逻辑删除)")
