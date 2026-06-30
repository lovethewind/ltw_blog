from __future__ import annotations

from typing import TYPE_CHECKING, Any

from starlette.websockets import WebSocket

from apps.base.enum.chat import WSMessageTypeEnum
from apps.web.core.websocket.message_handler.base_handler import BaseMessageHandler
from apps.web.dto.chat_dto import WSMessageDTO
from apps.web.dto.notice_dto import NoticeSaveDTO

if TYPE_CHECKING:
    from apps.web.core.websocket.manager import WebSocketManager


class NoticeHandler(BaseMessageHandler):
    """通知消息处理器。"""

    message_type = WSMessageTypeEnum.NOTICE

    def validate(self, message: dict[str, Any] | WSMessageDTO[Any]) -> WSMessageDTO[NoticeSaveDTO]:
        """
        校验通知消息。

        :param message: 原始或已解析消息
        :return: 通知消息
        """
        return WSMessageDTO[NoticeSaveDTO].model_validate(message)

    async def handle(
        self,
        manager: WebSocketManager,
        websocket: WebSocket | None,
        message: WSMessageDTO[NoticeSaveDTO],
        user_id: int | None,
    ) -> None:
        """
        向通知接收用户发送消息。

        :param manager: WebSocket Manager
        :param websocket: 消息来源连接
        :param message: 通知消息
        :param user_id: 已认证用户 ID
        :return: None
        """
        await manager.publish_message(message, [message.message.user_id])
