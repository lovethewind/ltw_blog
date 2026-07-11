from __future__ import annotations

from typing import TYPE_CHECKING, Any

from starlette.websockets import WebSocket

from apps.base.core.depend_inject import GetBean
from apps.base.enum.chat import ChatMessageFailReasonEnum, ContactTypeEnum, MessageSendStatusEnum, WSMessageTypeEnum
from apps.web.config.logger_config import logger
from apps.web.core.websocket.message_handler.base_handler import BaseMessageHandler
from apps.web.dto.chat_dto import (
    ChatMessageDTO,
    ChatSaveMessageDTO,
    ChatSendMessageDTO,
    GroupProfileDTO,
    WSMessageDTO,
)
from apps.web.dto.user_dto import UserBaseInfoDTO

if TYPE_CHECKING:
    from apps.web.core.websocket.manager import WebSocketManager


class ChatMessageHandler(BaseMessageHandler):
    """聊天消息处理器。"""

    message_type = WSMessageTypeEnum.CHAT_MESSAGE
    client_allowed = True

    def validate(self, message: dict[str, Any] | WSMessageDTO[Any]) -> WSMessageDTO[ChatSendMessageDTO]:
        """
        校验聊天发送消息。

        :param message: 原始或已解析消息
        :return: 聊天发送消息
        """
        return WSMessageDTO[ChatSendMessageDTO].model_validate(message)

    async def handle(
        self,
        manager: WebSocketManager,
        websocket: WebSocket | None,
        message: WSMessageDTO[ChatSendMessageDTO],
        user_id: int | None,
    ) -> None:
        """
        处理聊天消息。

        :param manager: WebSocket Manager
        :param websocket: 消息来源连接
        :param message: 聊天发送消息
        :param user_id: 已认证用户 ID
        :return: None
        """
        if user_id is None:
            raise ValueError("聊天消息必须来自已认证连接")
        message.message.user_id = user_id
        try:
            from apps.web.dao.chat_dao import ChatDao

            chat_dao = GetBean(ChatDao)
            if await self._is_direct_message_blocked(chat_dao, message.message):
                await self._publish_fail_message(manager, message, user_id, ChatMessageFailReasonEnum.BLOCKED)
                return
            save_message = ChatSaveMessageDTO.model_validate(message.message, from_attributes=True)
            db_message = await chat_dao.save_message(save_message)
            result = WSMessageDTO[ChatMessageDTO](
                message_type=WSMessageTypeEnum.CHAT_MESSAGE,
                message=ChatMessageDTO.model_validate(db_message, from_attributes=True),
            )
            result.message.temp_id = message.message.temp_id
            if result.message.contact_type == ContactTypeEnum.GROUP:
                await self._handle_group_message(manager, result)
                return
            await self._handle_direct_message(manager, result)
        except Exception as exc:
            await self._publish_fail_message(manager, message, user_id, ChatMessageFailReasonEnum.SYSTEM_ERROR)
            logger.exception(f"聊天消息发送失败: {exc}")

    async def _publish_fail_message(
        self,
        manager: WebSocketManager,
        message: WSMessageDTO[ChatSendMessageDTO],
        user_id: int,
        fail_reason: ChatMessageFailReasonEnum,
    ) -> None:
        """
        发布聊天消息发送失败回执。

        :param manager: WebSocket Manager
        :param message: 聊天发送消息
        :param user_id: 已认证用户 ID
        :param fail_reason: 失败原因
        :return: None
        """
        message.message.status = MessageSendStatusEnum.FAIL
        message.message.fail_reason = fail_reason
        await manager.publish_message(message, [user_id])

    async def _is_direct_message_blocked(self, chat_dao: Any, message: ChatSendMessageDTO) -> bool:
        """
        判断单聊消息是否被双方黑名单关系拦截。

        :param chat_dao: 聊天 DAO
        :param message: 聊天发送消息
        :return: 是否被黑名单关系拦截
        """
        if message.contact_type != ContactTypeEnum.USER:
            return False
        return await chat_dao.is_blocked(message.user_id, message.contact_id) or await chat_dao.is_blocked(
            message.contact_id,
            message.user_id,
        )

    async def _handle_direct_message(
        self,
        manager: WebSocketManager,
        message: WSMessageDTO[ChatMessageDTO],
    ) -> None:
        """
        处理单聊消息。

        :param manager: WebSocket Manager
        :param message: 已保存的聊天消息
        :return: None
        """
        from apps.web.utils.redis_util import WebRedisUtil

        redis_util = GetBean(WebRedisUtil)
        recipient_id = message.message.contact_id
        message.message.is_read = await manager.store.is_in_conversation(
            recipient_id,
            message.message.conversation_id,
        )
        if not message.message.is_read:
            await redis_util.Chat.incr_conversation_unread_count(
                recipient_id,
                message.message.conversation_id,
            )
        message.message.user_profile = await manager.get_user_info(
            message.message.user_id,
            UserBaseInfoDTO,
        )
        await manager.publish_message(
            message,
            [message.message.user_id, recipient_id],
        )

    async def _handle_group_message(
        self,
        manager: WebSocketManager,
        message: WSMessageDTO[ChatMessageDTO],
    ) -> None:
        """
        处理群聊消息，并按用户生成已读状态。

        :param manager: WebSocket Manager
        :param message: 已保存的聊天消息
        :return: None
        """
        from apps.web.dao.chat_dao import ChatDao
        from apps.web.utils.redis_util import WebRedisUtil

        chat_dao = GetBean(ChatDao)
        redis_util = GetBean(WebRedisUtil)
        member_ids = set(await chat_dao.get_group_members(message.message.contact_id))
        member_ids.add(message.message.user_id)
        group_profile = await manager.get_group_info(
            message.message.contact_id,
            GroupProfileDTO,
        )
        for member_id in member_ids:
            user_message = message.model_copy(deep=True)
            user_message.message.group_profile = group_profile
            user_message.message.is_read = (
                member_id == message.message.user_id
                or await manager.store.is_in_conversation(
                    member_id,
                    message.message.conversation_id,
                )
            )
            if not user_message.message.is_read:
                await redis_util.Chat.incr_conversation_unread_count(
                    member_id,
                    message.message.conversation_id,
                )
            await manager.publish_message(user_message, [member_id])
