from __future__ import annotations

from typing import TYPE_CHECKING, Any

from starlette.websockets import WebSocket

from apps.base.enum.chat import WSMessageTypeEnum
from apps.web.core.websocket.message_handler.base_handler import BaseMessageHandler
from apps.web.dto.chat_dto import FriendApplyMessageDTO, WSMessageDTO

if TYPE_CHECKING:
    from apps.web.core.websocket.manager import WebSocketManager


class FriendApplyHandler(BaseMessageHandler):
    """好友申请消息处理器。"""

    message_type = WSMessageTypeEnum.FRIEND_APPLY

    def validate(self, message: dict[str, Any] | WSMessageDTO[Any]) -> WSMessageDTO[FriendApplyMessageDTO]:
        """
        校验好友申请消息。

        :param message: 原始或已解析消息
        :return: 好友申请消息
        """
        return WSMessageDTO[FriendApplyMessageDTO].model_validate(message)

    async def handle(
        self,
        manager: WebSocketManager,
        websocket: WebSocket | None,
        message: WSMessageDTO[FriendApplyMessageDTO],
        user_id: int | None,
    ) -> None:
        """
        向好友申请接收用户发送消息。

        :param manager: WebSocket Manager
        :param websocket: 消息来源连接
        :param message: 好友申请消息
        :param user_id: 已认证用户 ID
        :return: None
        """
        await manager.publish_message(message, [message.message.user_id])
