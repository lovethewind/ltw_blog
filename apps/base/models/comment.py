from sqlalchemy import BigInteger, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.constant.common_constant import CommonConstant
from apps.base.core.sqlalchemy.base_model import BaseModel
from apps.base.enum.action import ObjectTypeEnum
from apps.base.enum.comment import CommentStatusEnum


class Comment(BaseModel):
    """
    评论模型。
    """

    __tablename__ = "t_comment"
    __table_args__ = (
        Index("idx_user_together", "user_id", "obj_type", "status"),
        Index("idx_obj_together", "obj_id", "obj_type", "status"),
        {"comment": "评论表"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, comment="评论用户id")
    obj_id: Mapped[int] = mapped_column(BigInteger, comment="评论对象id")
    obj_type: Mapped[int] = mapped_column(
        Integer, default=ObjectTypeEnum.ARTICLE.value, comment="评论对象类型 1:文章 5:图片"
    )
    parent_id: Mapped[int] = mapped_column(BigInteger, default=CommonConstant.TOP_LEVEL, comment="父id")
    reply_user_id: Mapped[int] = mapped_column(
        BigInteger, default=CommonConstant.TOP_LEVEL, comment="回复的评论所属用户id, 便于查询组装结果"
    )
    first_level_id: Mapped[int] = mapped_column(
        BigInteger, default=CommonConstant.TOP_LEVEL, comment="第一层级评论id, 方便查询"
    )
    content: Mapped[str] = mapped_column(Text, comment="评论内容")
    status: Mapped[int] = mapped_column(
        Integer, default=CommentStatusEnum.PASS.value, comment="评论状态 1:通过 2:审核中 3:已删除"
    )
