# @Time    : 2024/11/4 13:57
# @Author  : frank
# @File    : chat_service.py
import asyncio
from datetime import datetime

from sqlalchemy import func, or_, select

from apps.base.core.depend_inject import Autowired, Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.chat import ContactApplyStatusEnum, ContactTypeEnum, WSMessageTypeEnum
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.chat import ChatMessage, Contact, ContactApplyRecord, Conversation
from apps.base.utils.redis_util import RedisUtil
from apps.web.core.context_vars import ContextVars
from apps.web.dao.chat_dao import ChatDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.chat_dto import (
    ChatMessageDTO,
    ChatMessageResultDTO,
    ContactApplyDTO,
    ContactDTO,
    ConversationDTO,
    FriendApplyMessageDTO,
    GroupProfileDTO,
    UserProfileDTO,
    WSMessageDTO,
)
from apps.web.utils.ws_util import manager
from apps.web.vo.chat_vo import (
    ContactApplyVO,
    ContactVO,
    ConversationUpdateVO,
    ConversationVO,
    HandleContactApplyVO,
    HistoryMessageVO,
)


@Component()
class ChatService:
    user_dao: UserDao = Autowired()
    chat_dao: ChatDao = Autowired()
    redis_util: RedisUtil = Autowired()

    async def list_conversation(self, current_page: int, page_size: int) -> dict:
        """
        获取会话列表

        :param current_page: 当前页码。
        :param page_size: 每页数量。
        :return: 会话分页数据。
        """
        user_id = ContextVars.token_user_id.get()
        filters = [Conversation.user_id == user_id, Conversation.is_clear.is_(False)]
        offset, limit = db.page(current_page, page_size)
        total, conversations = await asyncio.gather(
            db.scalar(select(func.count()).select_from(Conversation).where(*filters)),
            db.model_all(
                select(Conversation)
                .where(*filters)
                .order_by(Conversation.is_pinned.desc(), Conversation.last_view_time.desc())
                .offset(offset)
                .limit(limit)
            ),
        )
        records = ConversationDTO.bulk_model_validate(conversations)
        last_message_dict = await self.chat_dao.get_conversation_last_message(records)
        for conversation in records:
            if conversation.contact_type == ContactTypeEnum.USER:
                conversation.user_profile = await manager.get_user_info(conversation.contact_id)
            else:
                conversation.group_profile = await manager.get_group_info(conversation.contact_id)
            conversation.last_message = last_message_dict.get(conversation.conversation_id)
            conversation.online = await manager.is_online(conversation)
            conversation.unread_count = await self.redis_util.Chat.get_conversation_unread_count(
                user_id, conversation.conversation_id
            )
        return {"total": total, "records": records}

    async def get_conversation_detail(self, conversation_vo: ConversationVO) -> ConversationDTO:
        """
        获取会话详情

        :param conversation_vo: 会话查询参数。
        :return: 会话详情。
        """
        user_id = ContextVars.token_user_id.get()
        conversation = await db.model_first(
            select(Conversation).where(
                Conversation.user_id == user_id,
                Conversation.contact_id == conversation_vo.contact_id,
            )
        )
        if not conversation:
            conversation_id = manager.gen_conversation_id(
                user_id, conversation_vo.contact_id, conversation_vo.contact_type
            )
            conversation = await db.create(
                Conversation(
                    user_id=user_id,
                    contact_id=conversation_vo.contact_id,
                    contact_type=conversation_vo.contact_type,
                    conversation_id=conversation_id,
                )
            )
        if conversation.is_clear:
            conversation.is_clear = False
            async with db.atomic() as session:
                session.add(conversation)
                await session.flush()
        dto = ConversationDTO.model_validate(conversation, from_attributes=True)
        if dto.contact_type == ContactTypeEnum.USER:
            dto.user_profile = await manager.get_user_info(dto.contact_id)
        else:
            dto.group_profile = await manager.get_group_info(dto.contact_id)
        dto.online = await manager.is_online(dto)
        dto.unread_count = await self.redis_util.Chat.get_conversation_unread_count(
            user_id, conversation.conversation_id
        )
        last_message_dict = await self.chat_dao.get_conversation_last_message([conversation])
        dto.last_message = last_message_dict.get(dto.conversation_id)
        return dto

    async def list_message(self, history_message_vo: HistoryMessageVO) -> ChatMessageResultDTO:
        """
        获取消息列表

        :param history_message_vo: 历史消息查询参数。
        :return: 聊天消息结果。
        """
        user_id = ContextVars.token_user_id.get()
        dto = ChatMessageResultDTO(records=[])
        conversation = await db.model_first(
            select(Conversation).where(
                Conversation.user_id == user_id,
                Conversation.conversation_id == history_message_vo.conversation_id,
            )
        )
        if not conversation:
            return dto
        filters = [ChatMessage.conversation_id == history_message_vo.conversation_id]
        if conversation.last_clear_time:
            filters.append(ChatMessage.create_time > conversation.last_clear_time)
        if history_message_vo.next_message_id:
            filters.append(ChatMessage.id < history_message_vo.next_message_id)

        page_size = 20
        records = ChatMessageDTO.bulk_model_validate(
            await db.model_all(select(ChatMessage).where(*filters).order_by(ChatMessage.id.desc()).limit(page_size))
        )
        for message in records:
            user_info_id = message.contact_id if message.user_id == user_id else message.user_id
            message.user_profile = await manager.get_user_info(user_info_id)
            message.group_profile = await manager.get_group_info(message.contact_id)
        records.sort(key=lambda x: x.id)
        dto.records = records
        dto.next_message_id = records[0].id if records else None
        dto.no_more = len(records) < page_size
        return dto

    async def update_conversation(self, conversation_update_vo: ConversationUpdateVO) -> None:
        """
        更新会话信息

        :param conversation_update_vo: 会话更新参数。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        conversation_id = conversation_update_vo.conversation_id
        conversation = await db.model_first(
            select(Conversation).where(
                Conversation.user_id == user_id,
                Conversation.conversation_id == conversation_id,
            )
        )
        if not conversation:
            return
        update_dict = conversation_update_vo.model_dump(exclude_none=True, exclude={"all_read", "conversation_id"})
        async with db.atomic() as session:
            if conversation_update_vo.is_clear:
                update_dict.update(last_clear_time=datetime.now())
                await self.redis_util.Chat.reset_conversation_unread_count(user_id, conversation_id)
            if conversation_update_vo.all_read:
                update_dict.update(last_view_time=datetime.now(), unread_count=0, is_clear=False)
                await self.redis_util.Chat.reset_conversation_unread_count(user_id, conversation_id)
            for key, value in update_dict.items():
                setattr(conversation, key, value)
            session.add(conversation)
            await session.flush()

    async def contact_apply(self, contact_apply_vo: ContactApplyVO) -> None:
        """
        添加好友申请

        :param contact_apply_vo: 好友申请参数。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        if await self.chat_dao.is_blocked(contact_apply_vo.contact_id, user_id):
            return
        has_exists = await db.scalar(
            select(func.count())
            .select_from(ContactApplyRecord)
            .where(
                ContactApplyRecord.user_id == user_id,
                ContactApplyRecord.contact_id == contact_apply_vo.contact_id,
                ContactApplyRecord.contact_type == contact_apply_vo.contact_type,
                ContactApplyRecord.status == ContactApplyStatusEnum.PENDING,
            )
        )
        if has_exists:
            return
        record = await db.create(
            ContactApplyRecord(
                user_id=user_id,
                contact_id=contact_apply_vo.contact_id,
                contact_type=contact_apply_vo.contact_type,
                status=ContactApplyStatusEnum.PENDING,
                content=contact_apply_vo.content,
            )
        )
        # 申请后页面通知对方
        message = WSMessageDTO[FriendApplyMessageDTO](
            message_type=WSMessageTypeEnum.FRIEND_APPLY, message=FriendApplyMessageDTO(user_id=record.contact_id)
        )
        message.message.user_profile = await manager.get_user_info(record.user_id, UserProfileDTO)
        await manager.send_message(message)

    async def list_contact_apply(self) -> list[ContactApplyDTO]:
        """
        获取好友申请列表

        :return: 好友申请列表。
        """
        user_id = ContextVars.token_user_id.get()
        records = await db.model_all(
            select(ContactApplyRecord).where(
                or_(ContactApplyRecord.contact_id == user_id, ContactApplyRecord.user_id == user_id)
            )
        )
        records = ContactApplyDTO.bulk_model_validate(records)
        for record in records:
            user_info_id = record.contact_id if record.user_id == user_id else record.user_id
            record.user_profile = await manager.get_user_info(user_info_id)
        return records

    async def handle_contact_apply(self, handle_contact_apply_vo: HandleContactApplyVO) -> None:
        """
        处理好友申请

        :param handle_contact_apply_vo: 好友申请处理参数。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        record = await db.model_first(
            select(ContactApplyRecord).where(
                ContactApplyRecord.user_id == handle_contact_apply_vo.contact_id,
                ContactApplyRecord.contact_id == user_id,
            )
        )
        if not record:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        if record.status != ContactApplyStatusEnum.PENDING:
            return
        record.status = handle_contact_apply_vo.status
        async with db.atomic() as session:
            if handle_contact_apply_vo.status == ContactApplyStatusEnum.AGREE:
                session.add(
                    Contact(user_id=record.contact_id, contact_id=record.user_id, contact_type=record.contact_type)
                )
                await self.redis_util.Chat.add_contact(record.contact_id, record.user_id)
                if record.contact_type == ContactTypeEnum.USER:
                    session.add(
                        Contact(user_id=record.user_id, contact_id=record.contact_id, contact_type=record.contact_type)
                    )
                    await self.redis_util.Chat.add_contact(record.user_id, record.contact_id)
            # 操作后页面通知对方
            message = WSMessageDTO[FriendApplyMessageDTO](
                message_type=WSMessageTypeEnum.FRIEND_APPLY,
                message=FriendApplyMessageDTO(user_id=record.user_id, status=handle_contact_apply_vo.status),
            )
            message.message.user_profile = await manager.get_user_info(record.user_id, UserProfileDTO)
            await manager.send_message(message)
            session.add(record)
            await session.flush()

    async def list_contact(self, contact_type: ContactTypeEnum, current_page: int, page_size: int) -> dict:
        """
        获取好友列表

        :param contact_type: 联系人类型。
        :param current_page: 当前页码。
        :param page_size: 每页数量。
        :return: 联系人分页数据。
        """
        user_id = ContextVars.token_user_id.get()
        filters = [Contact.user_id == user_id, Contact.contact_type == contact_type]
        offset, limit = db.page(current_page, page_size)
        total, contacts = await asyncio.gather(
            db.scalar(select(func.count()).select_from(Contact).where(*filters)),
            db.model_all(select(Contact).where(*filters).offset(offset).limit(limit)),
        )
        records = ContactDTO.bulk_model_validate(contacts)
        for contact in records:
            contact.user_profile = await manager.get_user_info(contact.contact_id, UserProfileDTO)
            contact.group_profile = await manager.get_group_info(contact.contact_id, GroupProfileDTO)
        return {"total": total, "records": records}

    async def delete_contact(self, contact_vo: ContactVO) -> None:
        """
        删除好友

        :param contact_vo: 联系人参数。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        async with db.atomic() as session:
            await self.chat_dao.delete_contact(user_id, contact_vo.contact_id, session=session)
