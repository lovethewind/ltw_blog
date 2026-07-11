from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.constant.common_constant import CommonConstant
from apps.base.core.sqlalchemy.base_model import BaseModel


class Message(BaseModel):
    """
    留言模型。
    """

    __tablename__ = "t_message"
    __table_args__ = {"comment": "留言表"}

    user_id: Mapped[int] = mapped_column(BigInteger, default=CommonConstant.TOP_LEVEL, comment="用户id")
    avatar: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="头像")
    nickname: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="昵称")
    email: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="联系人邮箱")
    address: Mapped[str] = mapped_column(String(100), comment="地址")
    content: Mapped[str] = mapped_column(Text, comment="留言内容")
    parent_id: Mapped[int] = mapped_column(BigInteger, default=CommonConstant.TOP_LEVEL, comment="父id")
    reply_user_id: Mapped[int] = mapped_column(
        BigInteger, default=CommonConstant.TOP_LEVEL, comment="回复的评论所属用户id, 便于查询组装结果"
    )
    first_level_id: Mapped[int] = mapped_column(
        BigInteger, default=CommonConstant.TOP_LEVEL, comment="第一层级评论id, 方便查询"
    )
