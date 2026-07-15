from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.core.sqlalchemy.base_model import BaseModel
from apps.base.enum.article import ArticleStatusEnum


class Article(BaseModel):
    """
    文章模型。
    """

    __tablename__ = "t_article"
    __table_args__ = {"comment": "文章表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    title: Mapped[str] = mapped_column(String(100), comment="标题")
    cover: Mapped[str] = mapped_column(String(512), comment="封面")
    cover_thumb: Mapped[str] = mapped_column(String(512), default="", comment="封面缩略图")
    category_id: Mapped[int] = mapped_column(BigInteger, comment="分类id")
    tag_list: Mapped[list] = mapped_column(JSON, default=list, comment="标签id列表")
    attach_list: Mapped[list] = mapped_column(JSON, default=list, comment="附件列表")
    content: Mapped[str] = mapped_column(Text, comment="内容")
    is_markdown: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否是markdown")
    is_original: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否是原创")
    original_url: Mapped[str] = mapped_column(String(512), comment="原文链接")
    status: Mapped[int] = mapped_column(
        Integer, default=ArticleStatusEnum.DRAFT.value, comment="文章状态 1:草稿 2:已发布 3:待审核 4:回收站"
    )
    hot_score: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0, comment="热门分数")
    recommend_score: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0, comment="推荐分数")
    recommend_weight: Mapped[int] = mapped_column(Integer, default=0, comment="人工推荐权重")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已删除(实现逻辑删除)")
    edit_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="最后编辑时间")
