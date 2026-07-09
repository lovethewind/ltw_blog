from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.enum.common import CheckStatusEnum
from apps.base.models.base import BaseModel


class Website(BaseModel):
    """
    网站导航模型。
    """

    __tablename__ = "t_website"
    __table_args__ = {"comment": "网站导航表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    name: Mapped[str] = mapped_column(String(100), comment="网站名")
    category_id: Mapped[int] = mapped_column(BigInteger, comment="分类id")
    cover: Mapped[str] = mapped_column(String(300), comment="封面")
    introduce: Mapped[str] = mapped_column(String(1000), comment="简介")
    url: Mapped[str] = mapped_column(String(100), comment="url")
    index: Mapped[int] = mapped_column(Integer, default=100000, comment="排序")
    status: Mapped[int] = mapped_column(
        Integer, default=CheckStatusEnum.PASS.value, comment="审核状态: 1: 已通过 2:审核中 3:拒绝"
    )


class WebsiteCategory(BaseModel):
    """
    网站导航分类模型。
    """

    __tablename__ = "t_website_category"
    __table_args__ = {"comment": "网站导航分类表"}

    name: Mapped[str] = mapped_column(String(100), comment="分类名")
    index: Mapped[int] = mapped_column(Integer, default=100000, comment="排序")
