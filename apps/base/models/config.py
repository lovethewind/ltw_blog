from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.models.base import BaseModel


class Config(BaseModel):
    """
    配置模型。
    """

    __tablename__ = "t_config"
    __table_args__ = {"comment": "配置表"}

    name: Mapped[str] = mapped_column(String(50), comment="配置key")
    value: Mapped[str] = mapped_column(Text, comment="配置value")
    description: Mapped[str] = mapped_column(String(1000), default="", comment="配置说明")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否启用")
