# @Time    : 2024/11/4 14:54
# @Author  : frank
# @File    : chat_dao.py
from datetime import datetime
from typing import TypeVar, Iterable

from tortoise.transactions import in_transaction

from apps.base.core.depend_inject import Component, Autowired
from apps.base.enum.action import ObjectTypeEnum, ActionTypeEnum
from apps.base.models.action import Action
from apps.base.models.chat import ChatGroup, ChatMessage, Conversation, Contact
from apps.web.constant.sql_constant import SqlConstant
from apps.web.dao.common_dao import CommonDao
from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.chat_dto import GroupInfoDTO, ChatSaveMessageDTO, ChatMessageDTO

T = TypeVar("T", bound=BaseDTO)


@Component()
class ChatDao:
    common_dao: CommonDao = Autowired()
    conversation_cache: dict[int, set[str]] = {}

    async def get_group_info(self, group_id: int):
        """
        根据群id列表获取群信息
        :param group_id: 群id列表
        :return: 群信息
        """
        group_list = await ChatGroup.filter(id=group_id).first()
        return GroupInfoDTO.model_validate(group_list, from_attributes=True)

    async def get_group_members(self, group_id: int) -> list[int]:
        """
        获取群成员id列表
        :param group_id: 群id
        :return: 群成员id列表
        """
        return await ChatGroup.filter(id=group_id).values_list("member_ids", flat=True)

    async def get_conversation_last_message(self, records: list[Conversation]):
        """
        获取会话最后一条消息
        :param records: 会话id列表
        :return: 最后一条消息
        """
        if not records:
            return {}
        temp_table = ", ".join(tuple(
            f"ROW{(item.conversation_id, item.last_clear_time.strftime("%Y-%m-%d %H:%M:%S") if item.last_clear_time else 0)}"
            for item in records))
        sql = SqlConstant.CONVERSATION_LAST_MESSAGE_LIST % (temp_table,)
        ret = await self.common_dao.execute_sql_dto(sql, clazz=ChatMessageDTO)
        return {item.conversation_id: item for item in ret}

    async def save_message(self, message: ChatSaveMessageDTO):
        """
        保存消息至数据库
        :param message:
        :return:
        """
        await self._check_create_conversation(message)
        return await ChatMessage.create(**message.model_dump())

    async def is_friend(self, user_id: int, contact_id: int):
        """
        是否是好友
        :param user_id:
        :param contact_id:
        :return:
        """
        return await Contact.filter(user_id=user_id, contact_id=contact_id).exists()

    async def is_blocked(self, user_id: int, contact_id: int):
        """
        是否已拉黑
        :param user_id:
        :param contact_id:
        :return:
        """
        return await Action.filter(user_id=user_id, obj_id=contact_id, obj_type=ObjectTypeEnum.USER,
                                   action_type=ActionTypeEnum.BLACKLIST, status=True).exists()

    async def delete_contact(self, user_id: int, contact_id: int):
        """
        删除联系人
        :param user_id:
        :param contact_id:
        :return:
        """
        await Contact.filter(user_id=user_id, contact_id=contact_id).delete()
        await Contact.filter(user_id=contact_id, contact_id=user_id).delete()

    async def _check_create_conversation(self, message: ChatSaveMessageDTO):
        """
        检查是否需要创建会话
        :param message: 消息
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
            async with in_transaction():
                conversation = await Conversation.get_or_none(**save_dict)
                if not conversation:
                    await Conversation.create(**save_dict)
            self.conversation_cache[message.contact_id].add(message.conversation_id)
