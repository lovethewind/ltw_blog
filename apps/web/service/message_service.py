import asyncio

from sqlalchemy import func, select

from apps.base.constant.common_constant import CommonConstant
from apps.base.core.depend_inject import Autowired, Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.message import Message
from apps.base.utils.ip_util import IpUtil
from apps.base.utils.picture_util import PictureUtil
from apps.web.core.context_vars import ContextVars
from apps.web.dto.message_dto import MessageDTO, UserBaseInfoDTO
from apps.web.utils.ws_util import manager
from apps.web.vo.message_vo import MessageAddVO


@Component()
class MessageService:
    picture_util: PictureUtil = Autowired()

    async def list_messages(self, current: int, size: int) -> dict:
        """
        获取留言板。

        :param current: 当前页码。
        :param size: 每页数量。
        :return: 留言分页结果。
        """
        offset, limit = db.page(current, size)
        total_stmt = select(func.count()).select_from(Message)
        first_level_count_stmt = (
            select(func.count()).select_from(Message).where(Message.first_level_id == CommonConstant.TOP_LEVEL)
        )
        first_level_stmt = (
            select(Message)
            .where(Message.first_level_id == CommonConstant.TOP_LEVEL)
            .order_by(Message.id.desc())
            .offset(offset)
            .limit(limit)
        )
        total, first_level_message_count, first_level_messages = await asyncio.gather(
            db.scalar(total_stmt),
            db.scalar(first_level_count_stmt),
            db.model_all(first_level_stmt),
        )
        first_level_messages_dto = []
        tourist_info_dict = {}
        message_ids = set()
        for message in first_level_messages:
            dto = MessageDTO.model_validate(message, from_attributes=True)
            message_ids.add(dto.id)
            if dto.user_id == CommonConstant.TOP_LEVEL:
                tourist_info_dict[dto.id] = UserBaseInfoDTO(
                    **{
                        "id": message.user_id,
                        "avatar": message.avatar,
                        "nickname": message.nickname,
                        "address": message.address,
                    }
                )
            first_level_messages_dto.append(dto)
        children_messages = []
        if message_ids:
            children_stmt = (
                select(Message)
                .where(Message.first_level_id.in_(message_ids))
                .order_by(Message.first_level_id, Message.id.desc())
            )
            children_candidates = await db.model_all(children_stmt)
            grouped_children: dict[int, list[Message]] = {}
            for child in children_candidates:
                grouped_children.setdefault(child.first_level_id, [])
                if len(grouped_children[child.first_level_id]) < 3:
                    grouped_children[child.first_level_id].append(child)
            children_messages = [child for children in grouped_children.values() for child in children]
        children_messages_dict: dict[int, list[MessageDTO]] = {}
        for message in children_messages:
            dto = MessageDTO.model_validate(message, from_attributes=True)
            message_ids.add(dto.id)
            if dto.user_id == CommonConstant.TOP_LEVEL:  # 给游客组装user属性
                tourist_info_dict[dto.id] = UserBaseInfoDTO(
                    id=message.user_id,
                    avatar=message.avatar,
                    nickname=message.nickname,
                    address=message.address,
                )
            if dto.first_level_id not in children_messages_dict:
                children_messages_dict[dto.first_level_id] = []
            children_messages_dict[dto.first_level_id].append(dto)
        # 查询所有一级留言子留言数量
        children_messages_count = []
        if message_ids:
            count_stmt = (
                select(Message.first_level_id, func.count(Message.id))
                .where(Message.first_level_id.in_(message_ids))
                .group_by(Message.first_level_id)
            )
            children_messages_count = await db.all(count_stmt)
        children_messages_count_dict = dict(children_messages_count)
        for message in first_level_messages_dto:
            if message.user_id == CommonConstant.TOP_LEVEL:  # 游客
                message.user = tourist_info_dict.get(message.id)
            else:
                message.user = await manager.get_user_info(message.user_id, UserBaseInfoDTO)
            message.children = children_messages_dict.get(message.id, [])
            message.children_count = children_messages_count_dict.get(message.id, 0)
            for child in message.children:
                if child.user_id == CommonConstant.TOP_LEVEL:  # 游客
                    child.user = tourist_info_dict.get(child.id)
                else:
                    child.user = await manager.get_user_info(child.user_id, UserBaseInfoDTO)
                if child.first_level_id != child.parent_id:  # 回复的是子留言
                    if child.reply_user_id == CommonConstant.TOP_LEVEL:  # 游客
                        child.reply_user = tourist_info_dict.get(child.id)
                    else:
                        child.reply_user = await manager.get_user_info(child.reply_user_id, UserBaseInfoDTO)
        return {"total": total, "records": first_level_messages_dto, "mainTotal": first_level_message_count}

    async def list_children_message(self, message_id: int, current: int, size: int) -> dict:
        """
        获取留言的子留言。

        :param message_id: 一级留言 ID。
        :param current: 当前页码。
        :param size: 每页数量。
        :return: 子留言分页结果。
        """
        offset, limit = db.page(current, size)
        count_stmt = select(func.count()).select_from(Message).where(Message.first_level_id == message_id)
        message_stmt = (
            select(Message)
            .where(Message.first_level_id == message_id)
            .order_by(Message.id.desc())
            .offset(offset)
            .limit(limit)
        )
        total, messages = await asyncio.gather(
            db.scalar(count_stmt),
            db.model_all(message_stmt),
        )
        records = MessageDTO.bulk_model_validate(messages)
        message_ids = set()
        tourist_reply_ids = set()
        tourist_info_dict = {}
        for message in records:
            message_ids.add(message.id)
            if message.reply_user_id == CommonConstant.TOP_LEVEL:
                tourist_reply_ids.add(message.id)
            if message.user_id == CommonConstant.TOP_LEVEL:
                tourist_info_dict[message.id] = UserBaseInfoDTO(
                    **{
                        "id": message.user_id,
                        "avatar": message.avatar,
                        "nickname": message.nickname,
                        "address": message.address,
                    }
                )
        # 查询游客的信息
        tourist_reply_ids = tourist_reply_ids - message_ids
        if tourist_reply_ids:
            tourist_stmt = select(Message).where(Message.id.in_(tourist_reply_ids))
            tourist_messages = await db.model_all(tourist_stmt)
            tourist_info_dict.update(
                {
                    message.id: UserBaseInfoDTO(
                        **{
                            "id": message.user_id,
                            "avatar": message.avatar,
                            "nickname": message.nickname,
                            "address": message.address,
                        }
                    )
                    for message in tourist_messages
                }
            )
        for message in records:
            if message.user_id == CommonConstant.TOP_LEVEL:  # 游客
                message.user = tourist_info_dict.get(message.id)
            else:
                message.user = await manager.get_user_info(message.user_id, UserBaseInfoDTO)
            if message.first_level_id != message.parent_id:  # 回复的是子留言
                if message.reply_user_id == CommonConstant.TOP_LEVEL:  # 游客
                    message.reply_user = tourist_info_dict.get(message.id)
                else:
                    message.reply_user = await manager.get(message.reply_user_id, UserBaseInfoDTO)
        return {"total": total, "records": records}

    async def add(self, message_add_vo: MessageAddVO) -> MessageDTO:
        """
        添加留言。

        :param message_add_vo: 留言提交参数。
        :return: 留言 DTO。
        """
        user_id = ContextVars.token_user_id.get()
        request = ContextVars.request.get()
        if not user_id and not message_add_vo.nickname:  # 未登录用户昵称必填
            raise MyException(ErrorCode.PARAM_ERROR)
        message = Message(**message_add_vo.model_dump(exclude_none=True))
        message.address = IpUtil.get_address_from_request(request)
        message.user_id = user_id or CommonConstant.TOP_LEVEL
        if not message.avatar and not user_id:
            message.avatar = await self.picture_util.get_random_avatar_url(only_thumb=True)  # noqa
        message = await db.create(message)
        ret = MessageDTO.model_validate(message, from_attributes=True)
        return ret
