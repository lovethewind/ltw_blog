# @Time    : 2024/8/28 11:20
# @Author  : frank
# @File    : comment_service.py
import asyncio
from datetime import datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import aliased

from apps.base.constant.common_constant import CommonConstant
from apps.base.core.depend_inject import Autowired, Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.action import ObjectTypeEnum
from apps.base.enum.comment import CommentStatusEnum
from apps.base.enum.error_code import ErrorCode
from apps.base.enum.notice import NoticeTypeEnum
from apps.base.enum.user import UserSettingsEnum
from apps.base.exception.my_exception import MyException
from apps.base.models.comment import Comment
from apps.base.utils.comment_count_util import sync_picture_comment_count
from apps.web.core.context_vars import ContextVars
from apps.web.core.kafka.util import KafkaUtil
from apps.web.dao.article_dao import ArticleDao
from apps.web.dao.picture_dao import PictureDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.chat_dto import WSMessageDTO
from apps.web.dto.comment_dto import CommentDTO
from apps.web.dto.notice_dto import NoticeSaveDTO
from apps.web.dto.user_dto import CachedUserInfoDTO, UserBaseInfoDTO
from apps.web.utils.redis_util import WebRedisUtil
from apps.web.utils.ws_util import manager
from apps.web.vo.comment_vo import CommentAddVO, CommentQueryVO


@Component()
class CommentService:
    user_dao: UserDao = Autowired()
    picture_dao: PictureDao = Autowired()
    article_dao: ArticleDao = Autowired()
    redis_util: WebRedisUtil = Autowired()
    kafka_util: KafkaUtil = Autowired()

    async def list_comments(self, current: int, size: int, comment_query_vo: CommentQueryVO) -> dict:
        """
        获取评论
        :param current:
        :param size:
        :param comment_query_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        # 第一层级评论
        filters = [
            Comment.obj_id == comment_query_vo.obj_id,
            Comment.obj_type == comment_query_vo.obj_type,
            Comment.status == CommentStatusEnum.PASS,
        ]
        first_level_filter = Comment.first_level_id == CommonConstant.TOP_LEVEL
        offset, limit = db.page(current, size)
        total, first_level_comment_count, first_level_comments = await asyncio.gather(
            db.scalar(select(func.count()).select_from(Comment).where(*filters)),
            db.scalar(select(func.count()).select_from(Comment).where(*filters, first_level_filter)),
            db.model_all(
                select(Comment)
                .where(*filters, first_level_filter)
                .order_by(Comment.id.desc())
                .offset(offset)
                .limit(limit)
            ),
        )
        first_level_comments = CommentDTO.bulk_model_validate(first_level_comments)
        comment_ids = [comment.id for comment in first_level_comments]
        children_comments = []
        children_comments_count = []
        if comment_ids:
            # 查出每条第一级评论的二级评论，默认前3条
            children_stmt = self._build_first_level_children_stmt(
                comment_query_vo.obj_id, comment_query_vo.obj_type, comment_ids
            )
            children_count_stmt = (
                select(Comment.first_level_id, func.count(Comment.id).label("comment_count"))
                .where(Comment.first_level_id.in_(comment_ids), Comment.status == CommentStatusEnum.PASS)
                .group_by(Comment.first_level_id)
            )
            children_comments, children_comments_count = await asyncio.gather(
                db.model_all(children_stmt),
                db.all(children_count_stmt),
            )
        children_comments_dict: dict[int, list[CommentDTO]] = {}
        for comment in children_comments:
            dto = CommentDTO.model_validate(comment, from_attributes=True)
            if dto.first_level_id not in children_comments_dict:
                children_comments_dict[dto.first_level_id] = []
            children_comments_dict[dto.first_level_id].append(dto)
        children_comments_count_dict = {item.first_level_id: item.comment_count for item in children_comments_count}
        # 查询出所有评论所属用户及回复的评论所属用户，供页面显示回复@xxx
        for comment in first_level_comments:
            comment.has_like = await self.redis_util.User.has_like_comment(user_id, comment.id)
            comment.like_count = await self.redis_util.Comment.get_comment_like_count(comment.id)
            comment.user = await manager.get_user_info(comment.user_id, UserBaseInfoDTO)
            comment.children = children_comments_dict.get(comment.id, [])
            comment.children_count = children_comments_count_dict.get(comment.id, 0)
            for child in comment.children:
                child.has_like = await self.redis_util.User.has_like_comment(user_id, child.id)
                child.like_count = await self.redis_util.Comment.get_comment_like_count(child.id)
                child.user = await manager.get_user_info(child.user_id, UserBaseInfoDTO)
                if child.first_level_id != child.parent_id:  # 回复的是子评论
                    child.reply_user = await manager.get_user_info(child.reply_user_id, UserBaseInfoDTO)
        return {"total": total, "records": first_level_comments, "mainTotal": first_level_comment_count}

    async def list_children_comment(self, comment_id: int, current: int, size: int) -> dict:
        """
        获取评论的子评论
        :param comment_id:
        :param current:
        :param size:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        offset, limit = db.page(current, size)
        filters = [Comment.first_level_id == comment_id, Comment.status == CommentStatusEnum.PASS]
        total, comments = await asyncio.gather(
            db.scalar(select(func.count()).select_from(Comment).where(*filters)),
            db.model_all(select(Comment).where(*filters).order_by(Comment.id.desc()).offset(offset).limit(limit)),
        )
        records = CommentDTO.bulk_model_validate(comments)
        for comment in records:
            comment.has_like = await self.redis_util.User.has_like_comment(user_id, comment.id)
            comment.like_count = await self.redis_util.Comment.get_comment_like_count(comment.id)
            comment.user = await manager.get_user_info(comment.user_id, UserBaseInfoDTO)
            if comment.first_level_id != comment.parent_id:  # 回复的是子评论
                comment.reply_user = await manager.get_user_info(comment.reply_user_id, UserBaseInfoDTO)
        return {"total": total, "records": records}

    async def add(self, comment_add_vo: CommentAddVO) -> CommentDTO:
        """
        添加评论

        :param comment_add_vo: 评论新增参数。
        :return: 新增评论 DTO。
        """
        user_id = ContextVars.token_user_id.get()
        await self._ensure_comment_allowed(user_id)
        comment = Comment(**comment_add_vo.model_dump())
        comment.user_id = user_id
        comment.status = CommentStatusEnum.PASS
        async with db.atomic() as session:
            session.add(comment)
            await session.flush()
            await sync_picture_comment_count(session, comment.obj_type, comment.obj_id, None, comment.status)
        if comment.obj_type == ObjectTypeEnum.ARTICLE:
            await self.redis_util.Article.incr_article_comment_count(comment.obj_id)
        ret = CommentDTO.model_validate(comment, from_attributes=True)
        asyncio.create_task(self._send_notice(user_id, comment_add_vo))
        return ret

    async def _ensure_comment_allowed(self, user_id: int) -> None:
        """
        校验用户当前是否允许发表评论。

        :param user_id: 用户 ID。
        :return: None。
        :raises MyException: 用户处于生效中的禁言状态时抛出。
        """
        user_info = await manager.get_user_info(user_id, CachedUserInfoDTO)
        restriction = user_info.user_restrictions.resolve(datetime.now())
        if restriction.comment_forbidden:
            raise MyException.error(ErrorCode.OPERATE_FAILED, "账号已被禁言，暂时无法评论")

    async def delete(self, comment_id: int) -> None:
        """
        根据评论id删除评论

        :param comment_id: 评论 ID。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        comment = await db.model_first(
            select(Comment).where(
                Comment.id == comment_id,
                Comment.user_id == user_id,
                Comment.status != CommentStatusEnum.DELETE,
            )
        )
        if not comment:
            return
        async with db.atomic() as session:
            result = await session.execute(
                update(Comment)
                .where(
                    Comment.id == comment.id,
                    Comment.user_id == user_id,
                    Comment.status != CommentStatusEnum.DELETE,
                )
                .values(status=CommentStatusEnum.DELETE)
            )
            if result.rowcount == 0:
                return
            await sync_picture_comment_count(
                session,
                comment.obj_type,
                comment.obj_id,
                comment.status,
                CommentStatusEnum.DELETE,
            )
        if comment.obj_type == ObjectTypeEnum.ARTICLE and comment.status == CommentStatusEnum.PASS:
            await self.redis_util.Article.incr_article_comment_count(comment.obj_id, -1)

    async def _send_notice(self, user_id: int, comment_add_vo: CommentAddVO) -> None:
        """
        发送评论通知。

        :param user_id: 评论用户 ID。
        :param comment_add_vo: 评论新增参数。
        :return: None。
        """
        setting_key = UserSettingsEnum.WHEN_COMMENT_MY_CONTENT
        notice_dto = NoticeSaveDTO()
        notice_dto.content = comment_add_vo.content
        notice_dto.detail.obj_id = comment_add_vo.obj_id
        notice_dto.detail.from_user_id = user_id
        notice_dto.detail.obj_type = comment_add_vo.obj_type
        if comment_add_vo.obj_type == ObjectTypeEnum.ARTICLE:
            article = await self.article_dao.get_article(comment_add_vo.obj_id)
            notice_dto.detail.obj_content = article.title
            notice_dto.user_id = article.user_id
            notice_dto.title = "评论了你的文章"
        elif comment_add_vo.obj_type == ObjectTypeEnum.PICTURE:
            picture = await self.picture_dao.get_picture(comment_add_vo.obj_id)
            notice_dto.detail.obj_content = picture.url
            notice_dto.user_id = picture.user_id
            notice_dto.title = "评论了你的图片"
        if comment_add_vo.parent_id == CommonConstant.TOP_LEVEL:
            notice_dto.notice_type = NoticeTypeEnum.COMMENT
        else:
            setting_key = UserSettingsEnum.WHEN_REPLY_MY_COMMENT
            notice_dto.title = "回复了你的评论"
            notice_dto.notice_type = NoticeTypeEnum.REPLY
            parent_comment = await db.model_first(select(Comment).where(Comment.id == comment_add_vo.parent_id))
            notice_dto.detail.comment_id = parent_comment.id
            notice_dto.detail.comment_content = parent_comment.content
            notice_dto.user_id = parent_comment.user_id
        user_setting_value = await self.user_dao.get_user_setting_value(notice_dto.user_id, setting_key)
        if user_setting_value is False:
            return
        if user_id == notice_dto.user_id:
            return
        await self.kafka_util.send_notice(notice_dto)
        notice_dto.detail.from_user = await manager.get_user_info(user_id, UserBaseInfoDTO)
        await manager.send_message(WSMessageDTO[NoticeSaveDTO](message=notice_dto))

    def _build_first_level_children_stmt(
        self, obj_id: int, obj_type: ObjectTypeEnum, comment_ids: list[int]
    ) -> Select[tuple[Comment]]:
        """
        构建一级评论下前三条子评论查询。

        :param obj_id: 对象 ID。
        :param obj_type: 对象类型。
        :param comment_ids: 一级评论 ID 列表。
        :return: SQLAlchemy 查询语句。
        """
        ranked_comments = (
            select(
                Comment,
                func.row_number()
                .over(partition_by=Comment.first_level_id, order_by=Comment.id.desc())
                .label("row_num"),
            )
            .where(
                Comment.obj_id == obj_id,
                Comment.obj_type == obj_type,
                Comment.first_level_id.in_(comment_ids),
                Comment.status == CommentStatusEnum.PASS,
            )
            .subquery()
        )
        comment_alias = aliased(Comment, ranked_comments)
        return select(comment_alias).where(ranked_comments.c.row_num <= 3)
