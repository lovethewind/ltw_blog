# @Time    : 2024/11/4 13:59
# @Author  : frank
# @File    : chat_dto.py
from tortoise import fields

from apps.base.enum.chat import ContactTypeEnum, ChatMessageTypeEnum, ChatGroupTypeEnum, ChatGroupJoinTypeEnum, \
    ChatGroupRoleEnum, ContactApplyStatusEnum
from apps.base.models.base import BaseModel


class Contact(BaseModel):
    user_id = fields.BigIntField(description="用户id")
    contact_id = fields.BigIntField(description="联系人id")
    contact_type = fields.IntEnumField(ContactTypeEnum, description="联系人类型")

    class Meta:
        table = "t_contact"
        table_description = "联系人表"


class Conversation(BaseModel):
    user_id = fields.BigIntField(description="用户id")
    contact_id = fields.BigIntField(description="联系人id")
    contact_type = fields.IntEnumField(ContactTypeEnum, description="联系人类型")
    conversation_id = fields.CharField(max_length=64, description="会话id")
    unread_count = fields.IntField(default=0, description="未读消息数量")
    is_pinned = fields.BooleanField(default=False, description="是否置顶")
    is_muted = fields.BooleanField(default=False, description="是否静音")
    is_clear = fields.BooleanField(default=False, description="是否清空")
    last_clear_time = fields.DatetimeField(null=True, description="上次清空时间")
    last_view_time = fields.DatetimeField(null=True, description="上次查看时间")

    class Meta:
        table = "t_conversation"
        table_description = "会话表"


class ChatMessage(BaseModel):
    user_id = fields.BigIntField(description="用户id")
    contact_id = fields.BigIntField(description="联系人id")
    contact_type = fields.IntEnumField(ContactTypeEnum, description="联系人类型")
    conversation_id = fields.CharField(max_length=64, description="会话id")
    content = fields.CharField(max_length=10000, description="消息内容")
    message_type = fields.IntEnumField(ChatMessageTypeEnum, default=ChatMessageTypeEnum.TEXT, description="消息类型")
    attach = fields.JSONField(default=[], description="附件列表")
    read_list = fields.JSONField(default=[], description="已读用户列表")
    delete_list = fields.JSONField(default=[], description="已删除用户列表")

    class Meta:
        table = "t_chat_message"
        table_description = "聊天消息表"


class ChatGroup(BaseModel):
    user_id = fields.BigIntField(description="群主id")
    name = fields.CharField(max_length=32, description="群名称")
    avatar = fields.CharField(max_length=512, description="群头像")
    notice = fields.CharField(max_length=1000, description="群公告")
    description = fields.CharField(max_length=1000, description="群描述")
    group_type = fields.IntEnumField(ChatGroupTypeEnum, default=ChatGroupTypeEnum.PUBLIC, description="群类型")

    class Meta:
        table = "t_chat_group"
        table_description = "群组表"


class ChatGroupMember(BaseModel):
    group_id = fields.BigIntField(description="群id")
    user_id = fields.BigIntField(description="用户id")
    role = fields.IntEnumField(ChatGroupRoleEnum, default=ChatGroupRoleEnum.MEMBER, description="成员角色")
    join_type = fields.IntEnumField(ChatGroupJoinTypeEnum, default=ChatGroupJoinTypeEnum.SEARCH, description="入群方式")
    remark = fields.CharField(max_length=1000, default="", description="加入详情")
    is_muted = fields.BooleanField(default=False, description="是否被禁言")

    class Meta:
        table = "t_chat_group_member"
        table_description = "群成员表"


class ContactApplyRecord(BaseModel):
    user_id = fields.BigIntField(description="用户id")
    contact_id = fields.BigIntField(description="联系人id")
    contact_type = fields.IntEnumField(ContactTypeEnum, description="联系人类型")
    content = fields.CharField(max_length=500, description="申请内容")
    status = fields.IntEnumField(ContactApplyStatusEnum, default=ContactApplyStatusEnum.PENDING, description="申请状态")

    class Meta:
        table = "t_contact_apply_record"
        table_description = "好友申请记录表"
