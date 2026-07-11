from sqlalchemy import JSON, BigInteger, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.core.sqlalchemy.base_model import BaseModel
from apps.base.enum.notice import NoticeTypeEnum


class Notice(BaseModel):
    """
    通知消息模型。
    """

    __tablename__ = "t_notice"
    __table_args__ = {"comment": "通知消息表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    title: Mapped[str] = mapped_column(String(255), comment="标题")
    content: Mapped[str] = mapped_column(Text, default="", comment="内容")
    notice_type: Mapped[int] = mapped_column(Integer, default=NoticeTypeEnum.SYSTEM.value, comment="消息类型")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已读")
    detail: Mapped[dict] = mapped_column(JSON, default=dict, comment="详情")
