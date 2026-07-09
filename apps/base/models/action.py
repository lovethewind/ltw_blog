from sqlalchemy import BigInteger, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.models.base import BaseModel


class Action(BaseModel):
    """
    动作记录，如点赞、喜欢、收藏、关注。
    """

    __tablename__ = "t_action"
    __table_args__ = {"comment": "行为表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    obj_id: Mapped[int] = mapped_column(BigInteger, comment="对象id")
    obj_type: Mapped[int] = mapped_column(Integer, comment="对象类型 1:文章 2:评论 3:用户")
    action_type: Mapped[int] = mapped_column(Integer, comment="动作类型 1:点赞 2:喜欢 3:收藏 4:关注")
    status: Mapped[bool] = mapped_column(Boolean, default=False, comment="状态 true:已XX false:未XX")


class ActionCount(BaseModel):
    """
    动作统计。
    """

    __tablename__ = "t_action_count"
    __table_args__ = {"comment": "行为统计表"}

    obj_id: Mapped[int] = mapped_column(BigInteger, comment="对象id")
    obj_type: Mapped[int] = mapped_column(Integer, comment="对象类型 1:文章 2:评论 3:用户")
    action_type: Mapped[int] = mapped_column(Integer, comment="动作类型 1:点赞 2:喜欢 3:收藏 4:关注 5:访问量 6:评论")
    count: Mapped[int] = mapped_column(Integer, default=0, comment="统计数量")
