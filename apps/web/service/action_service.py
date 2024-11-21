# @Time    : 2024/9/12 14:40
# @Author  : frank
# @File    : action_service.py
import asyncio

from tortoise.transactions import in_transaction

from apps.base.core.depend_inject import Component, Autowired
from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.enum.notice import NoticeTypeEnum
from apps.base.enum.user import UserSettingsEnum
from apps.base.models.action import Action
from apps.base.utils.page_util import Pagination, PageResult
from apps.base.utils.redis_util import RedisUtil
from apps.web.core.context_vars import ContextVars
from apps.web.core.kafka.util import KafkaUtil
from apps.web.dao.article_dao import ArticleDao
from apps.web.dao.chat_dao import ChatDao
from apps.web.dao.comment_dao import CommentDao
from apps.web.dao.picture_dao import PictureDao
from apps.web.dao.share_dao import ShareDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.action_dto import UserFollowInfoDTO, ActionDTO, BlckListDTO
from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.chat_dto import WSMessageDTO
from apps.web.dto.notice_dto import NoticeSaveDTO
from apps.web.dto.user_dto import UserBaseInfoDTO, UserSimpleInfoDTO
from apps.web.utils.ws_util import manager
from apps.web.vo.action_vo import ActionQueryVO, ActionAddVO, ActionTypeDetailQueryVO


@Component()
class ActionService:
    user_dao: UserDao = Autowired()
    article_dao: ArticleDao = Autowired()
    comment_dao: CommentDao = Autowired()
    picture_dao: PictureDao = Autowired()
    chat_dao: ChatDao = Autowired()
    share_dao: ShareDao = Autowired()
    redis_util: RedisUtil = Autowired()
    kafka_util: KafkaUtil = Autowired()

    async def list_actions(self, current: int, size: int, action_query_vo: ActionQueryVO,
                           action_type_detail_query_vo: ActionTypeDetailQueryVO):
        """
        获取行为列表
        :param current:
        :param size:
        :param action_query_vo:
        :param action_type_detail_query_vo:
        :return:
        """
        setting_key = None
        if action_query_vo.action_type == ActionTypeEnum.COLLECT:
            setting_key = UserSettingsEnum.ALLOW_VIEW_MY_COLLECT
        if action_query_vo.action_type == ActionTypeEnum.FOLLOW:
            setting_key = UserSettingsEnum.ALLOW_VIEW_MY_FOLLOW
        if setting_key:
            user_id = action_query_vo.user_id or action_query_vo.obj_id
            user_setting_value = await self.user_dao.get_user_setting_value(user_id, setting_key)
            if user_setting_value is False:
                return PageResult[ActionDTO](current=current, size=size, total=0, records=[])
        page = await self._get_action_type_data(current, size, action_query_vo, action_type_detail_query_vo)
        return page

    async def list_user_actions(self, current: int, size: int, action_query_vo: ActionQueryVO,
                                action_type_detail_query_vo: ActionTypeDetailQueryVO):
        """
        获取用户行为列表
        :param current:
        :param size:
        :param action_query_vo:
        :param action_type_detail_query_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        if ((action_query_vo.user_id and action_query_vo.user_id != user_id)
                or (action_query_vo.obj_id and action_query_vo.obj_id != user_id)):
            return PageResult[ActionDTO](current=current, size=size, total=0, records=[])
        page = await self._get_action_type_data(current, size, action_query_vo, action_type_detail_query_vo)
        return page

    async def add_or_update(self, action_add_vo: ActionAddVO):
        """
        添加行为
        :param action_add_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        action = await Action.filter(obj_id=action_add_vo.obj_id, obj_type=action_add_vo.obj_type,
                                     action_type=action_add_vo.action_type, user_id=user_id).first()
        if not action:
            action = Action(obj_id=action_add_vo.obj_id, obj_type=action_add_vo.obj_type,
                            action_type=action_add_vo.action_type, user_id=user_id, status=False)
            asyncio.create_task(self._send_notice(user_id, action))
        action.status = not action.status
        async with in_transaction():
            if action_add_vo.obj_type == ObjectTypeEnum.USER and action.action_type == ActionTypeEnum.BLACKLIST:
                if user_id == action_add_vo.obj_id:
                    return not action.status
                await self.chat_dao.delete_contact(user_id, action_add_vo.obj_id)
            await action.save()
            await self._action_type_cache(action)
        return action.status

    async def _send_notice(self, user_id: int, action: Action):
        setting_key = None
        notice_dto = NoticeSaveDTO()
        notice_dto.detail.from_user_id = user_id
        notice_dto.detail.obj_id = action.obj_id
        notice_dto.detail.obj_type = action.obj_type
        if action.action_type == ActionTypeEnum.LIKE:
            setting_key = UserSettingsEnum.WHEN_LIKE_MY_CONTENT
            notice_dto.notice_type = NoticeTypeEnum.LIKE
            if action.obj_type == ObjectTypeEnum.ARTICLE:
                article = await self.article_dao.get_article(action.obj_id)
                notice_dto.detail.obj_content = article.title
                notice_dto.user_id = article.user_id
                notice_dto.title = "点赞了你的文章"
            elif action.obj_type == ObjectTypeEnum.COMMENT:
                comment = await self.comment_dao.get_comment(action.obj_id)
                # 获取点赞的评论主体
                if comment.obj_type == ObjectTypeEnum.ARTICLE:
                    article = await self.article_dao.get_article(comment.obj_id)
                    notice_dto.detail.obj_id = article.id
                    notice_dto.detail.obj_content = article.title
                elif comment.obj_type == ObjectTypeEnum.SHARE:
                    share = await self.share_dao.get_share(comment.obj_id)
                    notice_dto.detail.obj_id = share.id
                    notice_dto.detail.obj_content = share.content
                elif comment.obj_type == ObjectTypeEnum.PICTURE:
                    picture = await self.picture_dao.get_picture(comment.obj_id)
                    notice_dto.detail.obj_id = picture.id
                    notice_dto.detail.obj_content = picture.url
                notice_dto.user_id = comment.user_id
                notice_dto.detail.comment_type = comment.obj_type
                notice_dto.detail.comment_id = comment.id
                notice_dto.detail.comment_content = comment.content
                notice_dto.title = "点赞了你的评论"
            elif action.obj_type == ObjectTypeEnum.SHARE:
                share = await self.share_dao.get_share(action.obj_id)
                notice_dto.detail.obj_content = share.content
                notice_dto.user_id = share.user_id
                notice_dto.title = "点赞了你的分享"
            elif action.obj_type == ObjectTypeEnum.PICTURE:
                picture = await self.picture_dao.get_picture(action.obj_id)
                notice_dto.detail.obj_content = picture.url
                notice_dto.user_id = picture.user_id
                notice_dto.title = "点赞了你的图片"
        elif action.action_type == ActionTypeEnum.COLLECT:
            setting_key = UserSettingsEnum.WHEN_COLLECT_MY_CONTENT
            notice_dto.notice_type = NoticeTypeEnum.COLLECT
            article = await self.article_dao.get_article(action.obj_id)
            notice_dto.user_id = article.user_id
            notice_dto.detail.obj_content = article.title
            notice_dto.title = "收藏了你的文章"
        elif action.action_type == ActionTypeEnum.FOLLOW:
            setting_key = UserSettingsEnum.WHEN_FOLLOW_ME
            notice_dto.notice_type = NoticeTypeEnum.FOLLOW
            user = await manager.get_user_info(action.obj_id, UserBaseInfoDTO)
            notice_dto.user_id = user.id
            notice_dto.detail.obj_content = user.nickname
            notice_dto.title = "关注了你"
        if setting_key:
            user_setting_value = await self.user_dao.get_user_setting_value(notice_dto.user_id, setting_key)
            if user_setting_value is False:
                return
        if user_id == notice_dto.user_id:
            return
        await self.kafka_util.send_notice(notice_dto)
        notice_dto.detail.from_user = await manager.get_user_info(user_id, UserBaseInfoDTO)
        await manager.send_message(WSMessageDTO[NoticeSaveDTO](message=notice_dto))

    async def _get_action_type_data(self, current: int, size: int, action_query_vo: ActionQueryVO,
                                    action_type_detail_query_vo: ActionTypeDetailQueryVO):
        """
        获取行为的实际数据
        :param current:
        :param size:
        :param action_query_vo:
        :param action_type_detail_query_vo:
        :return:
        """
        login_user_id = ContextVars.token_user_id.get()
        page = PageResult[BaseDTO](records=[], total=0, current=current, size=size)
        q = Action.filter(**action_query_vo.model_dump(exclude_none=True), status=True)
        if action_query_vo.action_type == ActionTypeEnum.COLLECT:
            page = await Pagination[Action](current, size, q).execute()
            # todo 支持查询
            article_ids = [action.obj_id for action in page.records]
            action_time_dict = {action.obj_id: action.create_time for action in page.records}
            page.records = await self.article_dao.get_article_detail_by_ids(article_ids=article_ids)
            for dto in page.records:
                dto.create_time = action_time_dict.get(dto.id)  # 获取收藏时间
        elif action_query_vo.action_type == ActionTypeEnum.FOLLOW:
            page = await Pagination[Action](current, size, q).execute()
            # 查询关注或者粉丝列表
            user_ids = [action.obj_id if action_query_vo.user_id else action.user_id for action in page.records]
            ret = []
            for user_id in user_ids:
                dto = await manager.get_user_info(user_id, UserFollowInfoDTO)
                dto.is_followed = await self.redis_util.Action.is_followed(login_user_id, dto.id)
                dto.is_my_fans = await self.redis_util.Action.is_fans(login_user_id, dto.id)
                ret.append(dto)
            page.records = ret
        elif action_query_vo.action_type == ActionTypeEnum.BLACKLIST:
            q = q.filter(user_id=login_user_id)
            page = await Pagination[Action](current, size, q).execute()
            ret = []
            for record in page.records:
                dto = BlckListDTO.model_validate(record, from_attributes=True)
                dto.user_profile = await manager.get_user_info(dto.obj_id, UserSimpleInfoDTO)
                ret.append(dto)
            page.records = ret

        return page

    async def _action_type_cache(self, action: Action):
        """
        缓存行为数据至redis
        :param action:
        :return:
        """
        if action.action_type == ActionTypeEnum.LIKE:
            if action.obj_type == ObjectTypeEnum.ARTICLE:
                await self.redis_util.Article.add_or_remove_article_like(action.user_id, action.obj_id)
            elif action.obj_type == ObjectTypeEnum.COMMENT:
                await self.redis_util.Comment.add_or_remove_comment_like(action.user_id, action.obj_id)
            elif action.obj_type == ObjectTypeEnum.SHARE:
                await self.redis_util.Share.add_or_remove_share_like(action.user_id, action.obj_id)
            elif action.obj_type == ObjectTypeEnum.PICTURE:
                await self.redis_util.Picture.add_or_remove_picture_like(action.user_id, action.obj_id)
        elif action.action_type == ActionTypeEnum.COLLECT:
            await self.redis_util.Article.add_or_remove_article_collect(action.user_id, action.obj_id)
        elif action.action_type == ActionTypeEnum.FOLLOW:
            await self.redis_util.Action.add_or_remove_follow(action.user_id, action.obj_id)
