import asyncio

from sqlalchemy import func, select

from apps.base.core.depend_inject import Autowired, Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.enum.notice import NoticeTypeEnum
from apps.base.enum.user import UserSettingsEnum
from apps.base.models.action import Action
from apps.base.models.comment import Comment
from apps.web.core.context_vars import ContextVars
from apps.web.core.kafka.util import KafkaUtil
from apps.web.dao.article_dao import ArticleDao
from apps.web.dao.chat_dao import ChatDao
from apps.web.dao.picture_dao import PictureDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.action_dto import BlckListDTO, UserFollowInfoDTO
from apps.web.dto.chat_dto import WSMessageDTO
from apps.web.dto.notice_dto import NoticeSaveDTO
from apps.web.dto.user_dto import UserBaseInfoDTO, UserSimpleInfoDTO
from apps.web.utils.redis_util import WebRedisUtil
from apps.web.utils.ws_util import manager
from apps.web.vo.action_vo import ActionAddVO, ActionQueryVO, ActionTypeDetailQueryVO


@Component()
class ActionService:
    user_dao: UserDao = Autowired()
    article_dao: ArticleDao = Autowired()
    picture_dao: PictureDao = Autowired()
    chat_dao: ChatDao = Autowired()
    redis_util: WebRedisUtil = Autowired()
    kafka_util: KafkaUtil = Autowired()

    async def list_actions(
        self,
        current: int,
        size: int,
        action_query_vo: ActionQueryVO,
        action_type_detail_query_vo: ActionTypeDetailQueryVO,
    ) -> dict:
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
            if not user_id:
                return {"total": 0, "records": []}
            user_setting_value = await self.user_dao.get_user_setting_value(user_id, setting_key)
            user_setting_value = bool(user_setting_value)
            if not user_setting_value:
                return {"total": 0, "records": []}
        page = await self._get_action_type_data(current, size, action_query_vo, action_type_detail_query_vo)
        return page

    async def list_user_actions(
        self,
        current: int,
        size: int,
        action_query_vo: ActionQueryVO,
        action_type_detail_query_vo: ActionTypeDetailQueryVO,
    ) -> dict:
        """
        获取用户行为列表
        :param current:
        :param size:
        :param action_query_vo:
        :param action_type_detail_query_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        if (action_query_vo.user_id and action_query_vo.user_id != user_id) or (
            action_query_vo.obj_id and action_query_vo.obj_id != user_id
        ):
            return {"total": 0, "records": []}
        page = await self._get_action_type_data(current, size, action_query_vo, action_type_detail_query_vo)
        return page

    async def add_or_update(self, action_add_vo: ActionAddVO) -> bool:
        """
        添加行为

        :param action_add_vo: 行为新增参数。
        :return: 切换后的行为状态。
        """
        user_id = ContextVars.token_user_id.get()
        action = await db.model_first(
            select(Action).where(
                Action.obj_id == action_add_vo.obj_id,
                Action.obj_type == action_add_vo.obj_type,
                Action.action_type == action_add_vo.action_type,
                Action.user_id == user_id,
            )
        )
        if not action:
            action = Action(
                obj_id=action_add_vo.obj_id,
                obj_type=action_add_vo.obj_type,
                action_type=action_add_vo.action_type,
                user_id=user_id,
                status=False,
            )
            asyncio.create_task(self._send_notice(user_id, action))
        action.status = not action.status
        async with db.atomic() as session:
            if action_add_vo.obj_type == ObjectTypeEnum.USER and action.action_type == ActionTypeEnum.BLACKLIST:
                if user_id == action_add_vo.obj_id:
                    return not action.status
                await self.chat_dao.delete_contact(user_id, action_add_vo.obj_id)
            session.add(action)
            await self._action_type_cache(action)
        return action.status

    async def _send_notice(self, user_id: int, action: Action) -> None:
        """
        发送行为通知。

        :param user_id: 行为发起用户 ID。
        :param action: 行为记录。
        :return: None。
        """
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
                comment = await self._get_comment(action.obj_id)
                # 获取点赞的评论主体
                if comment.obj_type == ObjectTypeEnum.ARTICLE:
                    article = await self.article_dao.get_article(comment.obj_id)
                    notice_dto.detail.obj_id = article.id
                    notice_dto.detail.obj_content = article.title
                elif comment.obj_type == ObjectTypeEnum.PICTURE:
                    picture = await self.picture_dao.get_picture(comment.obj_id)
                    notice_dto.detail.obj_id = picture.id
                    notice_dto.detail.obj_content = picture.url
                notice_dto.user_id = comment.user_id
                notice_dto.detail.comment_type = comment.obj_type
                notice_dto.detail.comment_id = comment.id
                notice_dto.detail.comment_content = comment.content
                notice_dto.title = "点赞了你的评论"
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

    async def _get_comment(self, comment_id: int) -> Comment | None:
        """
        根据评论 ID 获取评论。

        :param comment_id: 评论 ID。
        :return: 评论对象；不存在时返回 None。
        """
        return await db.model_first(select(Comment).where(Comment.id == comment_id))

    async def _get_action_type_data(
        self,
        current: int,
        size: int,
        action_query_vo: ActionQueryVO,
        action_type_detail_query_vo: ActionTypeDetailQueryVO,
    ) -> dict:
        """
        获取行为的实际数据
        :param current:
        :param size:
        :param action_query_vo:
        :param action_type_detail_query_vo:
        :return:
        """
        login_user_id = ContextVars.token_user_id.get()
        total = 0
        records = []
        filters = [
            getattr(Action, key) == value for key, value in action_query_vo.model_dump(exclude_none=True).items()
        ]
        stmt = select(Action).where(*filters, Action.status.is_(True))
        if action_query_vo.action_type == ActionTypeEnum.COLLECT:
            offset, limit = db.page(current, size)
            total, actions = await asyncio.gather(
                db.scalar(select(func.count()).select_from(stmt.subquery())),
                db.model_all(stmt.offset(offset).limit(limit)),
            )
            # todo 支持查询
            article_ids = [action.obj_id for action in actions]
            action_time_dict = {action.obj_id: action.create_time for action in actions}
            records = await self.article_dao.get_article_detail_by_ids(article_ids=article_ids)
            for dto in records:
                dto.collect_time = action_time_dict.get(dto.id)  # 获取收藏时间
        elif action_query_vo.action_type == ActionTypeEnum.FOLLOW:
            offset, limit = db.page(current, size)
            total, actions = await asyncio.gather(
                db.scalar(select(func.count()).select_from(stmt.subquery())),
                db.model_all(stmt.offset(offset).limit(limit)),
            )
            # 查询关注或者粉丝列表
            user_ids = [action.obj_id if action_query_vo.user_id else action.user_id for action in actions]
            ret = []
            for user_id in user_ids:
                dto = await manager.get_user_info(user_id, UserFollowInfoDTO)
                dto.is_followed = await self.redis_util.Action.is_followed(login_user_id, dto.id)
                dto.is_my_fans = await self.redis_util.Action.is_fans(login_user_id, dto.id)
                ret.append(dto)
            records = ret
        elif action_query_vo.action_type == ActionTypeEnum.BLACKLIST:
            stmt = stmt.where(Action.user_id == login_user_id)
            offset, limit = db.page(current, size)
            total, actions = await asyncio.gather(
                db.scalar(select(func.count()).select_from(stmt.subquery())),
                db.model_all(stmt.offset(offset).limit(limit)),
            )
            ret = []
            for record in actions:
                dto = BlckListDTO.model_validate(record, from_attributes=True)
                dto.user_profile = await manager.get_user_info(dto.obj_id, UserSimpleInfoDTO)
                ret.append(dto)
            records = ret

        return {"total": total, "records": records}

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
            elif action.obj_type == ObjectTypeEnum.PICTURE:
                await self.redis_util.Picture.add_or_remove_picture_like(action.user_id, action.obj_id)
        elif action.action_type == ActionTypeEnum.COLLECT:
            await self.redis_util.Article.add_or_remove_article_collect(action.user_id, action.obj_id)
        elif action.action_type == ActionTypeEnum.FOLLOW:
            await self.redis_util.Action.add_or_remove_follow(action.user_id, action.obj_id)
        elif action.action_type == ActionTypeEnum.BLACKLIST and action.obj_type == ObjectTypeEnum.USER:
            await self.redis_util.Chat.sync_blacklist(action.user_id, action.obj_id, action.status)
