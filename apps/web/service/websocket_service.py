# @Time    : 2024/11/4 17:56
# @Author  : frank
# @File    : websocket_service.py
from pydantic import ValidationError
from starlette.websockets import WebSocket, WebSocketDisconnect

from apps.base.core.depend_inject import Component
from apps.base.enum.chat import WSMessageTypeEnum
from apps.web.config.logger_config import logger
from apps.web.dto.chat_dto import WSMessageDTO, SystemMessageDTO, ChangeCurrentConversationMessageDTO, \
    ChatSendMessageDTO, FriendApplyMessageDTO
from apps.web.dto.notice_dto import NoticeSaveDTO
from apps.web.utils.ws_util import manager


@Component()
class WebSocketService:

    async def connect_system(self, websocket: WebSocket, user_id: int):
        websocket.scope["user_id"] = user_id
        await manager.connect(websocket)
        logger.info(f"【{user_id}】连接系统成功")
        while True:
            try:
                message = await websocket.receive_json()
                try:
                    msg = WSMessageDTO.model_validate(message)
                    if msg.message_type == WSMessageTypeEnum.NOTICE:
                        message = WSMessageDTO[NoticeSaveDTO].model_validate(message)
                    elif msg.message_type == WSMessageTypeEnum.SYSTEM_IN_TIME:
                        message = WSMessageDTO[SystemMessageDTO].model_validate(message)
                    elif msg.message_type == WSMessageTypeEnum.FRIEND_APPLY:
                        message = WSMessageDTO[FriendApplyMessageDTO].model_validate(message)
                    elif msg.message_type == WSMessageTypeEnum.CHAT_MESSAGE:
                        message = WSMessageDTO[ChatSendMessageDTO].model_validate(message)
                        message.message.user_id = user_id
                    elif msg.message_type == WSMessageTypeEnum.CHANGE_CURRENT_CONVERSATION:
                        message = WSMessageDTO[ChangeCurrentConversationMessageDTO].model_validate(message)
                        message.message.user_id = user_id
                    await manager.send_message(message)
                except ValidationError as e:
                    logger.info(f"无效的消息: {e}")
                    continue
            except WebSocketDisconnect as e:
                logger.info(f"【{user_id}】关闭连接系统")
                await manager.disconnect(websocket)
                break

    async def test(self, message: WSMessageDTO[SystemMessageDTO]):
        await manager.send_message(message)
