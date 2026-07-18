from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.core.sqlalchemy.base_model import BaseModel


class Note(BaseModel):
    """
    私人笔记模型。
    """

    __tablename__ = "t_note"
    __table_args__ = (
        Index("idx_note_user_list", "user_id", "is_deleted", "is_pinned", "update_time", "id"),
        {"comment": "私人笔记表"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="用户 ID")
    folder_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="文件夹 ID")
    title: Mapped[str] = mapped_column(String(100), default="无标题笔记", comment="标题")
    content: Mapped[str] = mapped_column(Text, default="", comment="Markdown 内容")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否置顶")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否在回收站")
    deleted_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="删除时间")
    deleted_by_folder_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="随文件夹删除的根文件夹 ID"
    )


class NoteHistory(BaseModel):
    """私人笔记历史版本模型。"""

    __tablename__ = "t_note_history"
    __table_args__ = (
        Index("idx_note_history_note_time", "note_id", "create_time", "id"),
        Index("idx_note_history_user", "user_id", "note_id"),
        {"comment": "私人笔记历史版本表"},
    )

    note_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="笔记 ID")
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="用户 ID")
    title: Mapped[str] = mapped_column(String(100), nullable=False, comment="历史标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="历史 Markdown 内容")
    folder_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="历史文件夹 ID")
    tag_ids: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False, comment="历史标签 ID 列表")


class NoteFolder(BaseModel):
    """
    私人笔记文件夹模型。
    """

    __tablename__ = "t_note_folder"
    __table_args__ = (
        UniqueConstraint("user_id", "parent_id", "name", name="uk_note_folder_user_parent_name"),
        Index("idx_note_folder_user_tree", "user_id", "is_deleted", "parent_id", "sort_order", "id"),
        {"comment": "私人笔记文件夹表"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="用户 ID")
    parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="父文件夹 ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="文件夹名称")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否在回收站")
    deleted_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="删除时间")
    deleted_root_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="删除操作的根文件夹 ID")


class NoteTag(BaseModel):
    """
    私人笔记标签模型。
    """

    __tablename__ = "t_note_tag"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uk_note_tag_user_name"),
        {"comment": "私人笔记标签表"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="用户 ID")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="标签名称")


class NoteTagRelation(BaseModel):
    """
    私人笔记与标签关联模型。
    """

    __tablename__ = "t_note_tag_relation"
    __table_args__ = (
        UniqueConstraint("note_id", "tag_id", name="uk_note_tag_relation_note_tag"),
        {"comment": "私人笔记标签关联表"},
    )

    note_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="笔记 ID")
    tag_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="标签 ID")
