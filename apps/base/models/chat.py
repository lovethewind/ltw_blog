from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.core.sqlalchemy.base_model import BaseModel
from apps.base.enum.chat import (
    ChatGroupJoinTypeEnum,
    ChatGroupRoleEnum,
    ChatGroupTypeEnum,
    ChatMessageTypeEnum,
    ContactApplyStatusEnum,
)


class Contact(BaseModel):
    """
    联系人模型。
    """

    __tablename__ = "t_contact"
    __table_args__ = {"comment": "联系人表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    contact_id: Mapped[int] = mapped_column(BigInteger, comment="联系人id")
    contact_type: Mapped[int] = mapped_column(Integer, comment="联系人类型")


class Conversation(BaseModel):
    """
    会话模型。
    """

    __tablename__ = "t_conversation"
    __table_args__ = {"comment": "会话表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    contact_id: Mapped[int] = mapped_column(BigInteger, comment="联系人id")
    contact_type: Mapped[int] = mapped_column(Integer, comment="联系人类型")
    conversation_id: Mapped[str] = mapped_column(String(64), comment="会话id")
    unread_count: Mapped[int] = mapped_column(Integer, default=0, comment="未读消息数量")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否置顶")
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否静音")
    is_clear: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否清空")
    last_clear_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="上次清空时间")
    last_view_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="上次查看时间")


class ChatMessage(BaseModel):
    """
    聊天消息模型。
    """

    __tablename__ = "t_chat_message"
    __table_args__ = {"comment": "聊天消息表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    contact_id: Mapped[int] = mapped_column(BigInteger, comment="联系人id")
    contact_type: Mapped[int] = mapped_column(Integer, comment="联系人类型")
    conversation_id: Mapped[str] = mapped_column(String(64), comment="会话id")
    content: Mapped[str] = mapped_column(String(10000), comment="消息内容")
    message_type: Mapped[int] = mapped_column(Integer, default=ChatMessageTypeEnum.TEXT.value, comment="消息类型")
    attach: Mapped[list] = mapped_column(JSON, default=list, comment="附件列表")
    read_list: Mapped[list] = mapped_column(JSON, default=list, comment="已读用户列表")
    delete_list: Mapped[list] = mapped_column(JSON, default=list, comment="已删除用户列表")


class ChatGroup(BaseModel):
    """
    群组模型。
    """

    __tablename__ = "t_chat_group"
    __table_args__ = {"comment": "群组表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="群主id")
    name: Mapped[str] = mapped_column(String(32), comment="群名称")
    avatar: Mapped[str] = mapped_column(String(512), comment="群头像")
    notice: Mapped[str] = mapped_column(String(1000), comment="群公告")
    description: Mapped[str] = mapped_column(String(1000), comment="群描述")
    group_type: Mapped[int] = mapped_column(Integer, default=ChatGroupTypeEnum.PUBLIC.value, comment="群类型")


class ChatGroupMember(BaseModel):
    """
    群成员模型。
    """

    __tablename__ = "t_chat_group_member"
    __table_args__ = {"comment": "群成员表"}

    group_id: Mapped[int] = mapped_column(BigInteger, comment="群id")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    role: Mapped[int] = mapped_column(Integer, default=ChatGroupRoleEnum.MEMBER.value, comment="成员角色")
    join_type: Mapped[int] = mapped_column(Integer, default=ChatGroupJoinTypeEnum.SEARCH.value, comment="入群方式")
    remark: Mapped[str] = mapped_column(String(1000), default="", comment="加入详情")
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否被禁言")


class ContactApplyRecord(BaseModel):
    """
    好友申请记录模型。
    """

    __tablename__ = "t_contact_apply_record"
    __table_args__ = {"comment": "好友申请记录表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    contact_id: Mapped[int] = mapped_column(BigInteger, comment="联系人id")
    contact_type: Mapped[int] = mapped_column(Integer, comment="联系人类型")
    content: Mapped[str] = mapped_column(String(500), comment="申请内容")
    status: Mapped[int] = mapped_column(Integer, default=ContactApplyStatusEnum.PENDING.value, comment="申请状态")
