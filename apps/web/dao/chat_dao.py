# @Time    : 2024/11/4 14:54
# @Author  : frank
# @File    : chat_dao.py
from types import SimpleNamespace
from typing import TypeVar

from sqlalchemy import delete, func, literal, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from apps.base.core.depend_inject import Autowired, Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.enum.chat import ContactTypeEnum
from apps.base.models.action import Action
from apps.base.models.chat import ChatGroup, ChatGroupMember, ChatMessage, Contact, Conversation
from apps.base.utils.redis_util import RedisUtil
from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.chat_dto import ChatMessageDTO, ChatSaveMessageDTO, ConversationDTO, GroupInfoDTO

T = TypeVar("T", bound=BaseDTO)


@Component()
class ChatDao:
    redis_util: RedisUtil = Autowired()
    conversation_cache: dict[int, set[str]] = {}

    async def get_group_info(self, group_id: int) -> GroupInfoDTO | dict:
        """
        根据群id列表获取群信息
        :param group_id: 群id列表
        :return: 群信息
        """
        group_list = await db.model_first(select(ChatGroup).where(ChatGroup.id == group_id))
        if not group_list:
            return {}
        return GroupInfoDTO.model_validate(group_list, from_attributes=True)

    async def get_group_members(self, group_id: int) -> list[int]:
        """
        获取群成员 ID 列表。

        :param group_id: 群组 ID
        :return: 群成员 ID 列表
        """
        return list(await db.model_all(select(ChatGroupMember.user_id).where(ChatGroupMember.group_id == group_id)))

    async def get_conversation_last_message(
        self, records: list[Conversation | ConversationDTO]
    ) -> dict[str, ChatMessageDTO]:
        """
        获取会话最后一条消息

        :param records: 会话列表。
        :return: 会话 ID 到最后一条消息的映射。
        """
        if not records:
            return {}

        conversation_scope = union_all(
            *[
                select(
                    literal(item.conversation_id).label("conversation_id"),
                    literal(item.last_clear_time).label("last_clear_time"),
                )
                for item in records
            ]
        ).subquery()
        ranked_messages = (
            select(
                ChatMessage.id,
                ChatMessage.user_id,
                ChatMessage.contact_id,
                ChatMessage.contact_type,
                ChatMessage.conversation_id,
                ChatMessage.content,
                ChatMessage.message_type,
                ChatMessage.attach,
                ChatMessage.create_time,
                func.row_number()
                .over(partition_by=ChatMessage.conversation_id, order_by=ChatMessage.id.desc())
                .label("row_num"),
            )
            .join(conversation_scope, ChatMessage.conversation_id == conversation_scope.c.conversation_id)
            .where(
                or_(
                    conversation_scope.c.last_clear_time.is_(None),
                    ChatMessage.create_time > conversation_scope.c.last_clear_time,
                )
            )
            .subquery()
        )
        ret = []
        async for row in db.stream_rows(select(ranked_messages).where(ranked_messages.c.row_num == 1)):
            if hasattr(row, "_mapping"):
                row = SimpleNamespace(**row._mapping)
            ret.append(ChatMessageDTO.model_validate(row, from_attributes=True))
        return {item.conversation_id: item for item in ret}

    async def save_message(self, message: ChatSaveMessageDTO) -> ChatMessage:
        """
        保存消息至数据库

        :param message: 待保存的消息。
        :return: 消息模型。
        """
        async with db.atomic() as session:
            await self._check_create_conversation(message, session=session)
            chat_message = ChatMessage(**message.model_dump())
            session.add(chat_message)
            await session.flush()
            return chat_message

    async def is_friend(self, user_id: int, contact_id: int) -> bool:
        """
        判断用户是否已添加指定好友，优先读取 Redis 缓存。

        :param user_id: 用户 ID
        :param contact_id: 联系人 ID
        :return: 是否是好友
        """
        if await self.redis_util.Chat.has_contact_cache(user_id):
            return await self.redis_util.Chat.is_friend(user_id, contact_id)
        contact_ids = list(
            await db.model_all(
                select(Contact.contact_id).where(
                    Contact.user_id == user_id,
                    Contact.contact_type == ContactTypeEnum.USER,
                )
            )
        )
        await self.redis_util.Chat.refresh_user_contacts(user_id, contact_ids)
        return contact_id in contact_ids

    async def is_blocked(self, user_id: int, contact_id: int) -> bool:
        """
        判断用户是否已拉黑指定联系人，优先读取 Redis 缓存。

        :param user_id: 用户 ID
        :param contact_id: 联系人 ID
        :return: 是否已拉黑
        """
        if await self.redis_util.Chat.has_blacklist_cache(user_id):
            return await self.redis_util.Chat.is_blocked(user_id, contact_id)
        contact_ids = list(
            await db.model_all(
                select(Action.obj_id).where(
                    Action.user_id == user_id,
                    Action.obj_type == ObjectTypeEnum.USER,
                    Action.action_type == ActionTypeEnum.BLACKLIST,
                    Action.status.is_(True),
                )
            )
        )
        await self.redis_util.Chat.refresh_user_blacklist(user_id, contact_ids)
        return contact_id in contact_ids

    async def delete_contact(self, user_id: int, contact_id: int, session: AsyncSession | None = None) -> None:
        """
        删除双方联系人并同步已存在的 Redis 联系人缓存。

        :param user_id: 用户 ID
        :param contact_id: 联系人 ID
        :param session: 可复用的数据库会话。
        :return: None
        """
        delete_current = delete(Contact).where(Contact.user_id == user_id, Contact.contact_id == contact_id)
        delete_reverse = delete(Contact).where(Contact.user_id == contact_id, Contact.contact_id == user_id)
        await db.execute(delete_current, session)
        await db.execute(delete_reverse, session)
        await self.redis_util.Chat.remove_contact(user_id, contact_id)
        await self.redis_util.Chat.remove_contact(contact_id, user_id)

    async def _check_create_conversation(
        self, message: ChatSaveMessageDTO, session: AsyncSession | None = None
    ) -> None:
        """
        检查是否需要创建会话

        :param message: 消息。
        :param session: 可复用的数据库会话。
        :return: None。
        """
        if message.contact_id not in self.conversation_cache:
            self.conversation_cache.setdefault(message.contact_id, set())
        if message.conversation_id not in self.conversation_cache[message.contact_id]:
            save_dict = {
                "conversation_id": message.conversation_id,
                "contact_id": message.user_id,
                "contact_type": message.contact_type,
                "user_id": message.contact_id,
            }
            stmt = select(Conversation).filter_by(**save_dict)
            if session:
                conversation = await session.scalar(stmt)
                if not conversation:
                    session.add(Conversation(**save_dict))
                    await session.flush()
            else:
                async with db.atomic() as session:
                    conversation = await session.scalar(stmt)
                    if not conversation:
                        session.add(Conversation(**save_dict))
                        await session.flush()
            self.conversation_cache[message.contact_id].add(message.conversation_id)
