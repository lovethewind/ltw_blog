# @Time    : 2024/9/5 16:46
# @Author  : frank
# @File    : share_service.py

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from apps.base.core.depend_inject import Component, Autowired
from apps.base.enum.action import ObjectTypeEnum
from apps.base.enum.common import CheckStatusEnum
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.share import Share
from apps.base.utils.page_util import Pagination
from apps.base.utils.redis_util import RedisUtil
from apps.web.core.context_vars import ContextVars
from apps.web.dao.comment_dao import CommentDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.share_dto import ShareDTO
from apps.web.dto.user_dto import UserBaseInfoDTO
from apps.web.utils.ws_util import manager
from apps.web.vo.batch_vo import BatchVO
from apps.web.vo.share_vo import ShareQueryVO, ShareAddVO, ShareUpdateVO


@Component()
class ShareService:
    redis_util: RedisUtil = Autowired()
    user_dao: UserDao = Autowired()
    comment_dao: CommentDao = Autowired()

    async def list_shares(self, current: int, size: int, share_query_vo: ShareQueryVO, is_user=False):
        """
        查询分享列表
        :param current:
        :param size:
        :param share_query_vo:
        :param is_user: 是否查询我的分享
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        q = Share.filter()
        if share_query_vo.keyword:
            q = q.filter(Q(content__icontains=share_query_vo.keyword) | Q(tag__contains=[share_query_vo.keyword]))
        if share_query_vo.tag:
            q = q.filter(tag__contains=[share_query_vo.tag])
        if share_query_vo.content:
            q = q.filter(content__icontains=share_query_vo.content)
        if share_query_vo.share_type:
            q = q.filter(share_type=share_query_vo.share_type)
        if is_user and user_id:
            q = q.filter(user_id=user_id, status__in=[CheckStatusEnum.PASS, CheckStatusEnum.CHECKING])
        else:
            q = q.filter(status=CheckStatusEnum.PASS)
        page = await Pagination[ShareDTO](current, size, q).execute()
        for share in page.records:
            share.like_count = await self.redis_util.Share.get_like_count(share.id)
            share.has_like = await self.redis_util.Share.has_like(user_id, share.id)
            share.user = await manager.get_user_info(share.user_id, UserBaseInfoDTO)
        return page

    async def add(self, share_add_vo: ShareAddVO):
        """
        添加分享
        :param share_add_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        save_dict = share_add_vo.model_dump(exclude_none=True)
        save_dict["tag"] = list(set(share_add_vo.tag))  # 去重
        share = Share(**save_dict)
        share.user_id = user_id
        share.status = CheckStatusEnum.PASS
        await share.save()

    async def update(self, share_update_vo: ShareUpdateVO):
        """
        更新分享
        :param share_update_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        share = await Share.filter(id=share_update_vo.id, user_id=user_id).first()
        if not share:
            raise MyException(ErrorCode.SHARE_NOT_EXIST)
        update_dict = share_update_vo.model_dump(exclude_none=True)
        if "tag" in update_dict:  # 去重
            update_dict["tag"] = list(set(share_update_vo.tag))
        await share.update_from_dict(update_dict)
        await share.save(update_fields=update_dict.keys())

    async def delete(self, batch_vo: BatchVO):
        """
        删除分享
        :param batch_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        q = Share.filter(id__in=batch_vo.ids, user_id=user_id)
        shares = await q.all()
        share_ids = [item.id for item in shares]
        async with in_transaction():
            # 删除评论
            await self.comment_dao.clear_comment(share_ids, obj_type=ObjectTypeEnum.SHARE)
            await q.delete()
