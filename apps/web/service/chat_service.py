# @Time    : 2024/11/4 13:57
# @Author  : frank
# @File    : chat_service.py
import asyncio
from datetime import datetime

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from apps.base.core.depend_inject import Component, Autowired
from apps.base.enum.chat import ContactApplyStatusEnum, ContactTypeEnum, WSMessageTypeEnum
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.chat import Conversation, ChatMessage, ContactApplyRecord, Contact
from apps.base.utils.redis_util import RedisUtil
from apps.web.core.context_vars import ContextVars
from apps.web.dao.chat_dao import ChatDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.chat_dto import ConversationDTO, ChatMessageDTO, ChatMessageResultDTO, ContactApplyDTO, ContactDTO, \
    UserProfileDTO, GroupProfileDTO, FriendApplyMessageDTO, WSMessageDTO
from apps.web.utils.ws_util import manager
from apps.web.vo.chat_vo import ConversationVO, HistoryMessageVO, ConversationUpdateVO, ContactApplyVO, \
    HandleContactApplyVO, ContactVO


@Component()
class ChatService:
    user_dao: UserDao = Autowired()
    chat_dao: ChatDao = Autowired()
    redis_util: RedisUtil = Autowired()

    async def list_conversation(self, current_page: int, page_size: int) -> dict:
        """
        获取会话列表
        :param current_page:
        :param page_size:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        q = Conversation.filter(user_id=user_id, is_clear=False).order_by("-is_pinned", "-last_view_time")
        current_page = current_page if current_page > 0 else 1
        page_size = page_size if page_size > 0 else 10
        total, conversations = await asyncio.gather(
            q.count(),
            q.page(current_page, page_size).all(),
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
            conversation.unread_count = await self.redis_util.Chat.get_conversation_unread_count(user_id,
                                                                                                 conversation.conversation_id)
        return {"total": total, "records": records}

    async def get_conversation_detail(self, conversation_vo: ConversationVO) -> ConversationDTO:
        """
        获取会话详情
        :param conversation_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        conversation = await Conversation.filter(user_id=user_id, contact_id=conversation_vo.contact_id).first()
        if not conversation:
            conversation_id = manager.gen_conversation_id(user_id, conversation_vo.contact_id,
                                                          conversation_vo.contact_type)
            conversation = await Conversation.create(user_id=user_id, contact_id=conversation_vo.contact_id,
                                                     contact_type=conversation_vo.contact_type,
                                                     conversation_id=conversation_id)
        if conversation.is_clear:
            conversation.is_clear = False
            await conversation.save(update_fields=("is_clear",))
        dto = ConversationDTO.model_validate(conversation, from_attributes=True)
        if dto.contact_type == ContactTypeEnum.USER:
            dto.user_profile = await manager.get_user_info(dto.contact_id)
        else:
            dto.group_profile = await manager.get_group_info(dto.contact_id)
        dto.online = await manager.is_online(dto)
        dto.unread_count = await self.redis_util.Chat.get_conversation_unread_count(user_id,
                                                                                    conversation.conversation_id)
        last_message_dict = await self.chat_dao.get_conversation_last_message([conversation])
        dto.last_message = last_message_dict.get(dto.conversation_id)
        return dto

    async def list_message(self, history_message_vo: HistoryMessageVO):
        """
        获取消息列表
        :param history_message_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        dto = ChatMessageResultDTO(records=[])
        conversation = await Conversation.filter(user_id=user_id,
                                                 conversation_id=history_message_vo.conversation_id).first()
        if not conversation:
            return dto
        q = ChatMessage.filter(conversation_id=history_message_vo.conversation_id).limit(20)
        if conversation.last_clear_time:
            q = q.filter(create_time__gt=conversation.last_clear_time)
        if history_message_vo.next_message_id:
            q = q.filter(id__lt=history_message_vo.next_message_id)
        records = ChatMessageDTO.bulk_model_validate(await q)
        for message in records:
            user_info_id = message.contact_id if message.user_id == user_id else message.user_id
            message.user_profile = await manager.get_user_info(user_info_id)
            message.group_profile = await manager.get_group_info(message.contact_id)
        records.sort(key=lambda x: x.id)
        dto.records = records
        dto.next_message_id = records[0].id if records else None
        dto.no_more = len(records) < 20
        return dto

    async def update_conversation(self, conversation_update_vo: ConversationUpdateVO):
        """
        更新会话信息
        :param conversation_update_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        conversation_id = conversation_update_vo.conversation_id
        conversation = await Conversation.filter(user_id=user_id, conversation_id=conversation_id).first()
        if not conversation:
            return
        update_dict = conversation_update_vo.model_dump(exclude_none=True, exclude={"all_read", "conversation_id"})
        async with in_transaction():
            if conversation_update_vo.is_clear:
                update_dict.update(last_clear_time=datetime.now())
                await self.redis_util.Chat.reset_conversation_unread_count(user_id, conversation_id)
            if conversation_update_vo.all_read:
                update_dict.update(last_view_time=datetime.now(), unread_count=0, is_clear=False)
                await self.redis_util.Chat.reset_conversation_unread_count(user_id, conversation_id)
            await conversation.update_from_dict(update_dict)
            await conversation.save(update_fields=update_dict.keys())

    async def contact_apply(self, contact_apply_vo: ContactApplyVO):
        """
        添加好友申请
        :param contact_apply_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        if await self.chat_dao.is_blocked(contact_apply_vo.contact_id, user_id):
            return
        has_exists = await ContactApplyRecord.filter(user_id=user_id, contact_id=contact_apply_vo.contact_id,
                                                     contact_type=contact_apply_vo.contact_type,
                                                     status=ContactApplyStatusEnum.PENDING).exists()
        if has_exists:
            return
        record = await ContactApplyRecord.create(user_id=user_id, contact_id=contact_apply_vo.contact_id,
                                                 contact_type=contact_apply_vo.contact_type,
                                                 status=ContactApplyStatusEnum.PENDING,
                                                 content=contact_apply_vo.content)
        # 申请后页面通知对方
        message = WSMessageDTO[FriendApplyMessageDTO](
            message_type=WSMessageTypeEnum.FRIEND_APPLY,
            message=FriendApplyMessageDTO(user_id=record.contact_id))
        message.message.user_profile = await manager.get_user_info(record.user_id, UserProfileDTO)
        await manager.send_message(message)

    async def list_contact_apply(self):
        """
        获取好友申请列表
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        records = await ContactApplyRecord.filter(Q(contact_id=user_id) | Q(user_id=user_id))
        records = ContactApplyDTO.bulk_model_validate(records)
        for record in records:
            user_info_id = record.contact_id if record.user_id == user_id else record.user_id
            record.user_profile = await manager.get_user_info(user_info_id)
        return records

    async def handle_contact_apply(self, handle_contact_apply_vo: HandleContactApplyVO):
        """
        处理好友申请
        :param handle_contact_apply_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        record = await ContactApplyRecord.filter(user_id=handle_contact_apply_vo.contact_id, contact_id=user_id).first()
        if not record:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        if record.status != ContactApplyStatusEnum.PENDING:
            return
        record.status = handle_contact_apply_vo.status
        async with in_transaction():
            if handle_contact_apply_vo.status == ContactApplyStatusEnum.AGREE:
                await Contact.create(user_id=record.contact_id, contact_id=record.user_id,
                                     contact_type=record.contact_type)
                if record.contact_type == ContactTypeEnum.USER:
                    await Contact.create(user_id=record.user_id, contact_id=record.contact_id,
                                         contact_type=record.contact_type)
            # 操作后页面通知对方
            message = WSMessageDTO[FriendApplyMessageDTO](
                message_type=WSMessageTypeEnum.FRIEND_APPLY,
                message=FriendApplyMessageDTO(user_id=record.user_id, status=handle_contact_apply_vo.status))
            message.message.user_profile = await manager.get_user_info(record.user_id, UserProfileDTO)
            await manager.send_message(message)
            await record.save(update_fields=("status", "update_time"))

    async def list_contact(self, contact_type: ContactTypeEnum, current_page: int, page_size: int) -> dict:
        """
        获取好友列表
        :param contact_type:
        :param current_page:
        :param page_size:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        q = Contact.filter(user_id=user_id, contact_type=contact_type)
        current_page = current_page if current_page > 0 else 1
        page_size = page_size if page_size > 0 else 10
        total, contacts = await asyncio.gather(
            q.count(),
            q.page(current_page, page_size).all(),
        )
        records = ContactDTO.bulk_model_validate(contacts)
        for contact in records:
            contact.user_profile = await manager.get_user_info(contact.contact_id, UserProfileDTO)
            contact.group_profile = await manager.get_group_info(contact.contact_id, GroupProfileDTO)
        return {"total": total, "records": records}

    async def delete_contact(self, contact_vo: ContactVO):
        """
        删除好友
        :param contact_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        async with in_transaction():
            await self.chat_dao.delete_contact(user_id, contact_vo.contact_id)
