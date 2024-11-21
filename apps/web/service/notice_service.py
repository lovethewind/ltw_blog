# @Time    : 2024/10/21 16:19
# @Author  : frank
# @File    : notice_service.py
from tortoise.functions import Count

from apps.base.core.depend_inject import Component, Autowired
from apps.base.enum.notice import NoticeTypeEnum
from apps.base.models.notice import Notice
from apps.base.utils.page_util import Pagination
from apps.web.core.context_vars import ContextVars
from apps.web.dao.user_dao import UserDao
from apps.web.dto.notice_dto import NoticeDTO
from apps.web.dto.user_dto import UserBaseInfoDTO
from apps.web.utils.ws_util import manager
from apps.web.vo.batch_vo import BatchVO


@Component()
class NoticeService:
    user_dao: UserDao = Autowired()

    async def get_unread_notice_count(self):
        """
        获取各类消息未读数量
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        count_info_list = await Notice.filter(user_id=user_id, is_read=False).group_by("notice_type").annotate(
            count=Count("id")).values("notice_type", "count")
        count_info_map = {item["notice_type"]: item["count"] for item in count_info_list}
        ret = {item.value: count_info_map.get(item.value, 0) for item in
               NoticeTypeEnum.__dict__["_member_map_"].values()}
        return ret

    async def get_notice_list(self, notice_type: NoticeTypeEnum, current: int, size: int):
        """
        获取消息列表
        :param notice_type:
        :param current:
        :param size:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        q = Notice.filter(user_id=user_id, notice_type=notice_type)
        page = await Pagination[NoticeDTO](current, size, q).execute()
        for item in page.records:
            item.detail.from_user = await manager.get_user_info(item.detail.from_user_id, UserBaseInfoDTO)
        return page

    async def update(self, batch_vo: BatchVO):
        """
        更新消息为已读
        :param batch_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        await Notice.filter(id__in=batch_vo.ids, user_id=user_id).update(is_read=True)

    async def delete(self, batch_vo: BatchVO):
        """
        删除消息
        :param batch_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        await Notice.filter(id__in=batch_vo.ids, user_id=user_id).delete()

    async def clear_notice(self, notice_type: NoticeTypeEnum):
        """
        清空消息
        :param notice_type:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        await Notice.filter(user_id=user_id, notice_type=notice_type).delete()
