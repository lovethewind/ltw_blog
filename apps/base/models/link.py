from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.core.sqlalchemy.base_model import BaseModel
from apps.base.enum.common import CheckStatusEnum


class Link(BaseModel):
    """
    友链模型。
    """

    __tablename__ = "t_link"
    __table_args__ = {"comment": "友链表"}

    name: Mapped[str] = mapped_column(String(100), comment="网站名")
    cover: Mapped[str] = mapped_column(String(300), comment="封面")
    introduce: Mapped[str] = mapped_column(String(1000), comment="简介")
    url: Mapped[str] = mapped_column(String(100), comment="url")
    email: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="联系人邮箱")
    index: Mapped[int] = mapped_column(Integer, default=100000, comment="排序")
    status: Mapped[int] = mapped_column(
        Integer, default=CheckStatusEnum.CHECKING.value, comment="审核状态: 1: 已通过 2:审核中 3:拒绝"
    )
    description: Mapped[str] = mapped_column(String(1000), default="", comment="说明")
