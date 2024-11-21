# @Time    : 2024/10/24 15:18
# @Author  : frank
# @File    : websocket_controller.py
from fastapi import APIRouter
from fastapi.params import Depends
from starlette.websockets import WebSocket

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.dto.chat_dto import WSMessageDTO, SystemMessageDTO
from apps.web.service.websocket_service import WebSocketService
from apps.web.utils.depends_util import DependsUtil

router = APIRouter(prefix="/ws", tags=["websocket模块"])


@Controller(router)
class WebsocketController:
    websocket_service: WebSocketService = Autowired()

    @router.websocket("/connectSystem")
    async def connect_system(self, websocket: WebSocket, user_id: int = Depends(DependsUtil.ws_user_id)):
        await self.websocket_service.connect_system(websocket, user_id)

    @router.post("/common/test")
    async def test(self, message: WSMessageDTO[SystemMessageDTO]):
        await self.websocket_service.test(message)
        return ResponseUtil.success()
