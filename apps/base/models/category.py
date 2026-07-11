from sqlalchemy import BigInteger, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.constant.common_constant import CommonConstant
from apps.base.core.sqlalchemy.base_model import BaseModel
from apps.base.enum.category import TagLevelEnum


class Category(BaseModel):
    """
    分类模型。
    """

    __tablename__ = "t_category"
    __table_args__ = {"comment": "分类表"}

    name: Mapped[str] = mapped_column(String(20), comment="分类名")
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="描述")
    index: Mapped[int] = mapped_column(Integer, default=100000, comment="排序(越小越在前)")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")


class Tag(BaseModel):
    """
    标签模型。
    """

    __tablename__ = "t_tag"
    __table_args__ = {"comment": "标签表"}

    name: Mapped[str] = mapped_column(String(20), comment="标签名")
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="描述")
    parent_id: Mapped[int] = mapped_column(BigInteger, default=CommonConstant.TOP_LEVEL, comment="所属父级")
    level: Mapped[int] = mapped_column(Integer, default=TagLevelEnum.CATEGORY.value, comment="层级(1:分类层 2:展示层)")
    index: Mapped[int] = mapped_column(Integer, default=100000, comment="排序(越小越在前)")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
