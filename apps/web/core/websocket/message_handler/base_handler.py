from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from starlette.websockets import WebSocket

from apps.base.enum.chat import WSMessageTypeEnum
from apps.web.dto.chat_dto import WSMessageDTO

if TYPE_CHECKING:
    from apps.web.core.websocket.manager import WebSocketManager


class BaseMessageHandler(ABC):
    """WebSocket 消息处理器基类。"""

    message_type: WSMessageTypeEnum
    client_allowed = False

    @abstractmethod
    def validate(self, message: dict[str, Any] | WSMessageDTO[Any]) -> WSMessageDTO[Any]:
        """
        校验并转换消息。

        :param message: 原始或已解析消息
        :return: 带具体消息体类型的消息
        """

    @abstractmethod
    async def handle(
        self,
        manager: "WebSocketManager",
        websocket: WebSocket | None,
        message: WSMessageDTO[Any],
        user_id: int | None,
    ) -> None:
        """
        处理消息。

        :param manager: WebSocket Manager
        :param websocket: 消息来源连接
        :param message: 已校验消息
        :param user_id: 已认证用户 ID
        :return: None
        """
