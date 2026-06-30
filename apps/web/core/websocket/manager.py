import asyncio
import logging
from collections.abc import Iterable
from contextlib import suppress
from typing import Any, Type, TypeVar
from uuid import uuid4

from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from starlette.websockets import WebSocket, WebSocketState

from apps.base.core.depend_inject import GetBean
from apps.base.enum.chat import ContactTypeEnum
from apps.web.core.websocket.data import WebSocketEnvelope
from apps.web.core.websocket.message_handler import (
    BaseMessageHandler,
    ChangeConversationHandler,
    ChatMessageHandler,
    FriendApplyHandler,
    NoticeHandler,
    SystemMessageHandler,
)
from apps.web.core.websocket.redis_store import WebSocketRedisStore
from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.chat_dto import ConversationDTO, GroupInfoDTO, WSMessageDTO
from apps.web.dto.user_dto import UserCommonInfoDTO

T = TypeVar("T", bound=BaseDTO)
logger = logging.getLogger(__name__)


class WebSocketManager:
    """支持 Redis 跨 worker 投递的 WebSocket Manager。"""

    def __init__(
            self,
            store: WebSocketRedisStore | Any | None = None,
            handlers: Iterable[BaseMessageHandler] | None = None,
            heartbeat_interval: int = 30,
    ) -> None:
        """
        初始化 WebSocket Manager。

        :param store: Redis 状态仓库
        :param handlers: 消息处理器列表
        :param heartbeat_interval: 连接状态续期间隔秒数
        :return: None
        """
        self.store = store or WebSocketRedisStore()
        default_handlers = handlers or (
            NoticeHandler(),
            ChatMessageHandler(),
            SystemMessageHandler(),
            ChangeConversationHandler(),
            FriendApplyHandler(),
        )
        self.handlers = {handler.message_type: handler for handler in default_handlers}
        self.heartbeat_interval = heartbeat_interval
        self._connections: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        self._subscriber_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._pubsub: Any | None = None

    async def connect(self, websocket: WebSocket) -> None:
        """
        接受并登记 WebSocket 连接。

        :param websocket: WebSocket 连接
        :return: None
        """
        await websocket.accept()
        user_id = websocket.scope.get("user_id")
        if not isinstance(user_id, int):
            raise ValueError("WebSocket 连接缺少用户 ID")
        connection_id = uuid4().hex
        websocket.scope["connection_id"] = connection_id
        async with self._lock:
            self._connections.setdefault(user_id, set()).add(websocket)
        try:
            await self.store.add_connection(user_id, connection_id)
        except Exception:
            async with self._lock:
                connections = self._connections.get(user_id)
                if connections:
                    connections.discard(websocket)
                    if not connections:
                        self._connections.pop(user_id, None)
            if websocket.client_state == WebSocketState.CONNECTED:
                with suppress(RuntimeError):
                    await websocket.close()
            raise

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        删除并关闭指定 WebSocket 连接。

        :param websocket: WebSocket 连接
        :return: None
        """
        user_id = websocket.scope.get("user_id")
        connection_id = websocket.scope.get("connection_id")
        if isinstance(user_id, int):
            async with self._lock:
                connections = self._connections.get(user_id)
                if connections:
                    connections.discard(websocket)
                    if not connections:
                        self._connections.pop(user_id, None)
            if isinstance(connection_id, str):
                try:
                    await self.store.remove_connection(user_id, connection_id)
                except Exception as e:
                    logger.exception(f"删除 WebSocket Redis 连接状态失败 {e}")
        if websocket.client_state == WebSocketState.CONNECTED:
            with suppress(RuntimeError):
                await websocket.close()

    async def handle_envelope(self, envelope: WebSocketEnvelope) -> None:
        """
        将 Redis 消息投递到本 worker 的匹配连接。

        :param envelope: 跨 worker 消息信封
        :return: None
        """
        async with self._lock:
            if envelope.target_user_ids is None:
                connections = [websocket for values in self._connections.values() for websocket in values]
            else:
                connections = [
                    websocket
                    for user_id in set(envelope.target_user_ids)
                    for websocket in self._connections.get(user_id, set())
                ]
        if connections:
            await asyncio.gather(
                *(websocket.send_json(envelope.payload) for websocket in connections),
                return_exceptions=True,
            )

    async def handle_client_message(
            self,
            websocket: WebSocket,
            message: dict[str, Any],
            user_id: int,
    ) -> None:
        """
        校验客户端消息并交给对应 Handler。

        :param websocket: 消息来源连接
        :param message: 原始消息
        :param user_id: 已认证用户 ID
        :return: None
        """
        base_message = WSMessageDTO[Any].model_validate(message)
        handler = self.handlers.get(base_message.message_type)
        if handler is None:
            raise ValueError(f"不支持的消息类型: {base_message.message_type}")
        if not handler.client_allowed:
            raise ValueError(f"客户端不能发送消息类型: {base_message.message_type}")
        validated_message = handler.validate(message)
        await handler.handle(self, websocket, validated_message, user_id)

    async def send_message(self, message: WSMessageDTO[Any]) -> None:
        """
        处理服务端产生的 WebSocket 消息。

        :param message: WebSocket 消息
        :return: None
        """
        handler = self.handlers.get(message.message_type)
        if handler is None:
            raise ValueError(f"不支持的消息类型: {message.message_type}")
        validated_message = handler.validate(message)
        await handler.handle(self, None, validated_message, None)

    async def publish_message(
            self,
            message: WSMessageDTO[Any],
            target_user_ids: list[int] | None = None,
    ) -> None:
        """
        通过 Redis 发布消息。

        :param message: WebSocket 消息
        :param target_user_ids: 目标用户 ID，None 表示广播
        :return: None
        """
        envelope = WebSocketEnvelope(
            payload=jsonable_encoder(message),
            target_user_ids=target_user_ids,
        )
        await self.store.publish(envelope)

    async def start(self) -> None:
        """
        启动 Redis 订阅和连接续期任务。

        :return: None
        """
        if self._subscriber_task and not self._subscriber_task.done():
            return
        await self._open_pubsub()
        self._subscriber_task = asyncio.create_task(self._subscribe(), name="websocket-redis-subscriber")
        self._heartbeat_task = asyncio.create_task(self._heartbeat(), name="websocket-connection-heartbeat")

    async def stop(self) -> None:
        """
        停止后台任务并清理本 worker 连接状态。

        :return: None
        """
        for task in (self._subscriber_task, self._heartbeat_task):
            if task:
                task.cancel()
        for task in (self._subscriber_task, self._heartbeat_task):
            if task:
                with suppress(asyncio.CancelledError):
                    await task
        await self._close_pubsub()
        async with self._lock:
            connections = [
                (user_id, websocket.scope.get("connection_id"))
                for user_id, values in self._connections.items()
                for websocket in values
            ]
        remove_tasks = [
            self.store.remove_connection(user_id, connection_id)
            for user_id, connection_id in connections
            if isinstance(connection_id, str)
        ]
        if remove_tasks:
            await asyncio.gather(*remove_tasks, return_exceptions=True)
        async with self._lock:
            self._connections.clear()
        self._subscriber_task = None
        self._heartbeat_task = None

    async def _open_pubsub(self) -> None:
        """
        创建并订阅 Redis Pub/Sub。

        :return: None
        """
        self._pubsub = self.store.get_redis().pubsub(ignore_subscribe_messages=True)
        await self._pubsub.subscribe(self.store.CHANNEL)

    async def _close_pubsub(self) -> None:
        """
        关闭当前 Redis Pub/Sub。

        :return: None
        """
        if self._pubsub is None:
            return
        with suppress(Exception):
            await self._pubsub.unsubscribe(self.store.CHANNEL)
        with suppress(Exception):
            await self._pubsub.aclose()
        self._pubsub = None

    async def _subscribe(self) -> None:
        """
        持续消费 Redis Pub/Sub 消息。

        :return: None
        """
        while True:
            try:
                if self._pubsub is None:
                    await self._open_pubsub()
                async for item in self._pubsub.listen():
                    if item.get("type") != "message":
                        continue
                    try:
                        envelope = WebSocketEnvelope.model_validate_json(item.get("data"))
                        await self.handle_envelope(envelope)
                    except TypeError, ValueError, ValidationError:
                        logger.warning("收到无效的 WebSocket Redis 消息")
                raise ConnectionError("WebSocket Redis 订阅已结束")
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.exception(f"WebSocket Redis 订阅异常，准备重连 {e}")
                await self._close_pubsub()
                await asyncio.sleep(1)

    async def _heartbeat(self) -> None:
        """
        定时续期本 worker 的连接状态。

        :return: None
        """
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            async with self._lock:
                connections = [
                    (user_id, connection_id)
                    for user_id, values in self._connections.items()
                    for websocket in values
                    if isinstance(connection_id := websocket.scope.get("connection_id"), str)
                ]
            try:
                await self.store.refresh_connections(connections)
            except Exception as e:
                logger.exception(f"WebSocket 连接状态续期失败 {e}")

    async def get_user_info(self, user_id: int, clazz: Type[T] = UserCommonInfoDTO) -> T:
        """
        获取 Redis 缓存的用户资料。

        :param user_id: 用户 ID
        :param clazz: 返回 DTO 类型
        :return: 用户资料 DTO
        """
        profile = await self.store.get_user_profile(user_id)
        if profile is None:
            from apps.web.dao.user_dao import UserDao

            user_dao = GetBean(UserDao)
            user_info = await user_dao.get_user_info(user_id)
            profile = jsonable_encoder(user_info)
            await self.store.set_user_profile(user_id, profile)
        return clazz.model_validate(profile)

    async def update_user_info(self, user_id: int) -> None:
        """
        更新 Redis 用户资料缓存。

        :param user_id: 用户 ID
        :return: None
        """
        from apps.web.dao.user_dao import UserDao

        user_dao = GetBean(UserDao)
        user_info = await user_dao.get_user_info(user_id)
        await self.store.set_user_profile(user_id, jsonable_encoder(user_info))

    async def get_group_info(self, group_id: int, clazz: Type[T] = GroupInfoDTO) -> T | None:
        """
        获取 Redis 缓存的群组资料。

        :param group_id: 群组 ID
        :param clazz: 返回 DTO 类型
        :return: 群组资料 DTO
        """
        profile = await self.store.get_group_profile(group_id)
        if profile is None:
            from apps.web.dao.chat_dao import ChatDao

            chat_dao = GetBean(ChatDao)
            group_info = await chat_dao.get_group_info(group_id)
            profile = jsonable_encoder(group_info)
            await self.store.set_group_profile(group_id, profile)
        if not profile:
            return None
        return clazz.model_validate(profile)

    async def update_group_info(self, group_id: int) -> None:
        """
        更新 Redis 群组资料缓存。

        :param group_id: 群组 ID
        :return: None
        """
        from apps.web.dao.chat_dao import ChatDao

        chat_dao = GetBean(ChatDao)
        group_info = await chat_dao.get_group_info(group_id)
        await self.store.set_group_profile(group_id, jsonable_encoder(group_info))

    async def is_online(self, conversation: ConversationDTO) -> bool:
        """
        判断会话联系人是否在线。

        :param conversation: 会话信息
        :return: 是否在线
        """
        if conversation.contact_type == ContactTypeEnum.GROUP:
            return True
        return await self.store.is_online(conversation.contact_id)

    def gen_conversation_id(self, user_id: int, contact_id: int, contact_type: ContactTypeEnum) -> str:
        """
        生成会话 ID。

        :param user_id: 当前用户 ID
        :param contact_id: 联系人或群组 ID
        :param contact_type: 联系类型
        :return: 会话 ID
        """
        if contact_type == ContactTypeEnum.GROUP:
            return str(contact_id)
        return "".join(sorted([str(user_id), str(contact_id)]))
