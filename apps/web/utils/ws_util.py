"""WebSocket Manager 兼容入口。"""

from apps.web.core.websocket.manager import WebSocketManager

ConnectManager = WebSocketManager
manager = WebSocketManager()

__all__ = ["ConnectManager", "manager"]
