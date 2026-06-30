from __future__ import annotations

from typing import TYPE_CHECKING, Any

from starlette.websockets import WebSocket

from apps.base.enum.chat import WSMessageTypeEnum
from apps.web.core.websocket.message_handler.base_handler import BaseMessageHandler
from apps.web.dto.chat_dto import ChangeCurrentConversationMessageDTO, WSMessageDTO

if TYPE_CHECKING:
    from apps.web.core.websocket.manager import WebSocketManager


class ChangeConversationHandler(BaseMessageHandler):
    """切换当前会话消息处理器。"""

    message_type = WSMessageTypeEnum.CHANGE_CURRENT_CONVERSATION
    client_allowed = True

    def validate(
        self,
        message: dict[str, Any] | WSMessageDTO[Any],
    ) -> WSMessageDTO[ChangeCurrentConversationMessageDTO]:
        """
        校验切换当前会话消息。

        :param message: 原始或已解析消息
        :return: 切换当前会话消息
        """
        return WSMessageDTO[ChangeCurrentConversationMessageDTO].model_validate(message)

    async def handle(
        self,
        manager: WebSocketManager,
        websocket: WebSocket | None,
        message: WSMessageDTO[ChangeCurrentConversationMessageDTO],
        user_id: int | None,
    ) -> None:
        """
        保存当前连接停留的会话。

        :param manager: WebSocket Manager
        :param websocket: 消息来源连接
        :param message: 切换当前会话消息
        :param user_id: 已认证用户 ID
        :return: None
        """
        if websocket is None or user_id is None:
            raise ValueError("切换当前会话消息必须来自已认证连接")
        connection_id = websocket.scope.get("connection_id")
        if not connection_id:
            raise ValueError("WebSocket 连接缺少 connection_id")
        await manager.store.set_current_conversation(
            user_id,
            connection_id,
            message.message.conversation_id,
        )
