"""模块化 WebSocket 支持。"""

from apps.web.core.websocket.data import WebSocketEnvelope
from apps.web.core.websocket.manager import WebSocketManager

__all__ = ["WebSocketEnvelope", "WebSocketManager"]
