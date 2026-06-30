from typing import Any

from pydantic import BaseModel, Field


class WebSocketEnvelope(BaseModel):
    """跨 worker 投递的 WebSocket 消息信封。"""

    payload: dict[str, Any]
    target_user_ids: list[int] | None = Field(default=None)
