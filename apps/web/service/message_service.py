# @Time    : 2024/9/4 16:41
# @Author  : frank
# @File    : message_service.py
import asyncio

from tortoise.functions import Count

from apps.base.constant.common_constant import CommonConstant
from apps.base.core.depend_inject import Component, Autowired
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.message import Message
from apps.base.utils.ip_util import IpUtil
from apps.base.utils.page_util import PageResult, Pagination
from apps.base.utils.picture_util import PictureUtil
from apps.web.constant.sql_constant import SqlConstant
from apps.web.core.context_vars import ContextVars
from apps.web.dao.common_dao import CommonDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.message_dto import MessageDTO, UserBaseInfoDTO
from apps.web.utils.ws_util import manager
from apps.web.vo.message_vo import MessageAddVO


@Component()
class MessageService:
    common_dao: CommonDao = Autowired()
    user_dao: UserDao = Autowired()
    picture_util: PictureUtil = Autowired()

    async def list_messages(self, current: int, size: int):
        """
        获取留言板
        :param current:
        :param size:
        :return:
        """
        # 第一层级评论
        q = Message.filter()
        (
            total,
            first_level_message_count,
            first_level_messages
        ) = await asyncio.gather(
            q.count(),
            q.filter(first_level_id=CommonConstant.TOP_LEVEL).count(),
            q.filter(first_level_id=CommonConstant.TOP_LEVEL).offset((current - 1) * size).limit(size)
        )
        first_level_messages_dto = []
        tourist_info_dict = {}
        tourist_reply_ids = set()
        message_ids = set()
        for message in first_level_messages:
            dto = MessageDTO.model_validate(message, from_attributes=True)
            message_ids.add(dto.id)
            if dto.user_id == CommonConstant.TOP_LEVEL:
                tourist_info_dict[dto.id] = UserBaseInfoDTO(**{
                    "id": message.user_id,
                    "avatar": message.avatar,
                    "nickname": message.nickname,
                    "address": message.address,
                })
            first_level_messages_dto.append(dto)
        children_messages = []
        if message_ids:
            # 查出每条第一级留言的二级留言，默认前3条
            children_messages = await self.common_dao.execute_sql(SqlConstant.FIRST_LEVEL_MESSAGE_3_CHILDREN_MESSAGE,
                                                                  (message_ids,))
        children_messages_dict: dict[int, list[MessageDTO]] = {}
        for message in children_messages:
            dto = MessageDTO.model_validate(message, from_attributes=True)
            message_ids.add(dto.id)
            if dto.reply_user_id == CommonConstant.TOP_LEVEL:  # 回复的是游客
                tourist_reply_ids.add(dto.id)
            if dto.user_id == CommonConstant.TOP_LEVEL:  # 给游客组装user属性
                tourist_info_dict[dto.id] = UserBaseInfoDTO(**message)
            if dto.first_level_id not in children_messages_dict:
                children_messages_dict[dto.first_level_id] = []
            children_messages_dict[dto.first_level_id].append(dto)
        # 查询所有一级留言子留言数量
        children_messages_count = (await Message.filter(first_level_id__in=message_ids)
                                   .annotate(count=Count("id"))
                                   .group_by("first_level_id")
                                   .values("count", "first_level_id"))
        children_messages_count_dict = {item["first_level_id"]: item["count"] for item in children_messages_count}
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
        page = PageResult(first_level_messages_dto, total=total, current=current, size=size)
        page.main_total = first_level_message_count
        return page

    async def list_children_message(self, message_id: int, current: int, size: int):
        """
        获取留言的子留言
        :param message_id:
        :param current:
        :param size:
        :return:
        """
        q = Message.filter(first_level_id=message_id)
        page = await Pagination[MessageDTO](current, size, q).execute()
        message_ids = set()
        tourist_reply_ids = set()
        tourist_info_dict = {}
        for message in page.records:
            message_ids.add(message.id)
            if message.reply_user_id == CommonConstant.TOP_LEVEL:
                tourist_reply_ids.add(message.id)
            if message.user_id == CommonConstant.TOP_LEVEL:
                tourist_info_dict[message.id] = UserBaseInfoDTO(**{
                    "id": message.user_id,
                    "avatar": message.avatar,
                    "nickname": message.nickname,
                    "address": message.address
                })
        # 查询游客的信息
        tourist_reply_ids = tourist_reply_ids - message_ids
        tourist_messages = await Message.filter(id__in=tourist_reply_ids).all()
        tourist_info_dict.update({message.id: UserBaseInfoDTO(**{
            "id": message.user_id,
            "avatar": message.avatar,
            "nickname": message.nickname,
            "address": message.address
        }) for message in tourist_messages})
        for message in page.records:
            if message.user_id == CommonConstant.TOP_LEVEL:  # 游客
                message.user = tourist_info_dict.get(message.id)
            else:
                message.user = await manager.get_user_info(message.user_id, UserBaseInfoDTO)
            if message.first_level_id != message.parent_id:  # 回复的是子留言
                if message.reply_user_id == CommonConstant.TOP_LEVEL:  # 游客
                    message.reply_user = tourist_info_dict.get(message.id)
                else:
                    message.reply_user = await manager.get(message.reply_user_id, UserBaseInfoDTO)
        return page

    async def add(self, message_add_vo: MessageAddVO):
        """
        添加留言
        :param message_add_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        request = ContextVars.request.get()
        if not user_id and not message_add_vo.nickname:  # 未登录用户昵称必填
            raise MyException(ErrorCode.PARAM_ERROR)
        message = Message(**message_add_vo.model_dump(exclude_none=True))
        message.address = IpUtil.get_address_from_request(request)
        message.user_id = user_id or CommonConstant.TOP_LEVEL
        if not message.avatar and not user_id:
            message.avatar = await self.picture_util.get_random_img_url(avatar=True)
        await message.save()
        ret = MessageDTO.model_validate(message, from_attributes=True)
        return ret
