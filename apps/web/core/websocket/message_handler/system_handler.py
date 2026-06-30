from __future__ import annotations

from typing import TYPE_CHECKING, Any

from starlette.websockets import WebSocket

from apps.base.enum.chat import WSMessageTypeEnum
from apps.web.core.websocket.message_handler.base_handler import BaseMessageHandler
from apps.web.dto.chat_dto import SystemMessageDTO, WSMessageDTO

if TYPE_CHECKING:
    from apps.web.core.websocket.manager import WebSocketManager


class SystemMessageHandler(BaseMessageHandler):
    """系统即时消息处理器。"""

    message_type = WSMessageTypeEnum.SYSTEM_IN_TIME

    def validate(self, message: dict[str, Any] | WSMessageDTO[Any]) -> WSMessageDTO[SystemMessageDTO]:
        """
        校验系统即时消息。

        :param message: 原始或已解析消息
        :return: 系统即时消息
        """
        return WSMessageDTO[SystemMessageDTO].model_validate(message)

    async def handle(
        self,
        manager: WebSocketManager,
        websocket: WebSocket | None,
        message: WSMessageDTO[SystemMessageDTO],
        user_id: int | None,
    ) -> None:
        """
        广播系统即时消息。

        :param manager: WebSocket Manager
        :param websocket: 消息来源连接
        :param message: 系统即时消息
        :param user_id: 已认证用户 ID
        :return: None
        """
        await manager.publish_message(message)
