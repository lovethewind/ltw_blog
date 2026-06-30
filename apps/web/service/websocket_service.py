# @Time    : 2024/11/4 17:56
# @Author  : frank
# @File    : websocket_service.py
from pydantic import ValidationError
from starlette.websockets import WebSocket, WebSocketDisconnect

from apps.base.core.depend_inject import Component
from apps.web.config.logger_config import logger
from apps.web.utils.ws_util import manager


@Component()
class WebSocketService:

    async def connect_system(self, websocket: WebSocket, user_id: int) -> None:
        """
        建立连接并将客户端消息交给对应 Handler。

        :param websocket: WebSocket 连接
        :param user_id: 已认证用户 ID
        :return: None
        """
        websocket.scope["user_id"] = user_id
        await manager.connect(websocket)
        logger.info(f"【{user_id}】连接系统成功")
        try:
            while True:
                message = await websocket.receive_json()
                try:
                    await manager.handle_client_message(websocket, message, user_id)
                except (ValidationError, ValueError) as exc:
                    logger.info(f"无效的消息: {exc}")
        except WebSocketDisconnect:
            logger.info(f"【{user_id}】关闭连接系统")
        finally:
            await manager.disconnect(websocket)
