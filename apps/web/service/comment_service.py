# @Time    : 2024/8/28 11:20
# @Author  : frank
# @File    : comment_service.py
import asyncio

from tortoise import transactions
from tortoise.functions import Count

from apps.base.constant.common_constant import CommonConstant
from apps.base.core.depend_inject import Component, Autowired
from apps.base.enum.action import ObjectTypeEnum
from apps.base.enum.comment import CommentStatusEnum
from apps.base.enum.notice import NoticeTypeEnum
from apps.base.enum.user import UserSettingsEnum
from apps.base.models.comment import Comment
from apps.base.utils.page_util import PageResult, Pagination
from apps.base.utils.redis_util import RedisUtil
from apps.web.constant.sql_constant import SqlConstant
from apps.web.core.context_vars import ContextVars
from apps.web.core.kafka.util import KafkaUtil
from apps.web.dao.article_dao import ArticleDao
from apps.web.dao.common_dao import CommonDao
from apps.web.dao.picture_dao import PictureDao
from apps.web.dao.share_dao import ShareDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.chat_dto import WSMessageDTO
from apps.web.dto.comment_dto import CommentDTO
from apps.web.dto.notice_dto import NoticeSaveDTO
from apps.web.dto.user_dto import UserBaseInfoDTO
from apps.web.utils.ws_util import manager
from apps.web.vo.comment_vo import CommentQueryVO, CommentAddVO


@Component()
class CommentService:
    common_dao: CommonDao = Autowired()
    user_dao: UserDao = Autowired()
    picture_dao: PictureDao = Autowired()
    article_dao: ArticleDao = Autowired()
    share_dao: ShareDao = Autowired()
    redis_util: RedisUtil = Autowired()
    kafka_util: KafkaUtil = Autowired()

    async def list_comments(self, current: int, size: int, comment_query_vo: CommentQueryVO):
        """
        获取评论
        :param current:
        :param size:
        :param comment_query_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        # 第一层级评论
        q = Comment.filter(obj_id=comment_query_vo.obj_id, obj_type=comment_query_vo.obj_type,
                           status=CommentStatusEnum.PASS)
        (
            total,
            first_level_comment_count,
            first_level_comments
        ) = await asyncio.gather(
            q.count(),
            q.filter(first_level_id=CommonConstant.TOP_LEVEL).count(),
            q.filter(first_level_id=CommonConstant.TOP_LEVEL).offset((current - 1) * size).limit(size)
        )
        first_level_comments = CommentDTO.bulk_model_validate(first_level_comments)
        comment_ids = []
        for comment in first_level_comments:
            comment_ids.append(comment.id)
        children_comments = []
        if comment_ids:
            # 查出每条第一级评论的二级评论，默认前3条
            children_comments = await self.common_dao.execute_sql(SqlConstant.FIRST_LEVEL_COMMENT_3_CHILDREN_COMMENT, (
                comment_query_vo.obj_id, comment_query_vo.obj_type.value, comment_ids, CommentStatusEnum.PASS.value))
        children_comments_dict: dict[int, list[CommentDTO]] = {}
        for comment in children_comments:
            dto = CommentDTO.model_validate(comment, from_attributes=True)
            if dto.first_level_id not in children_comments_dict:
                children_comments_dict[dto.first_level_id] = []
            children_comments_dict[dto.first_level_id].append(dto)
        # 查询所有一级评论子评论数量
        children_comments_count = (await Comment.filter(first_level_id__in=comment_ids, status=CommentStatusEnum.PASS)
                                   .annotate(count=Count("id"))
                                   .group_by("first_level_id")
                                   .values("count", "first_level_id"))
        children_comments_count_dict = {item["first_level_id"]: item["count"] for item in children_comments_count}
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
        page = PageResult(first_level_comments, total=total, current=current, size=size)
        page.main_total = first_level_comment_count
        return page

    async def list_children_comment(self, comment_id: int, current: int, size: int):
        """
        获取评论的子评论
        :param comment_id:
        :param current:
        :param size:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        q = Comment.filter(first_level_id=comment_id, status=CommentStatusEnum.PASS)
        page = await Pagination[CommentDTO](current, size, q).execute()
        for comment in page.records:
            comment.has_like = await self.redis_util.User.has_like_comment(user_id, comment.id)
            comment.like_count = await self.redis_util.Comment.get_comment_like_count(comment.id)
            comment.user = await manager.get_user_info(comment.user_id, UserBaseInfoDTO)
            if comment.first_level_id != comment.parent_id:  # 回复的是子评论
                comment.reply_user = await manager.get_user_info(comment.reply_user_id, UserBaseInfoDTO)
        return page

    async def add(self, comment_add_vo: CommentAddVO):
        """
        添加评论
        :param comment_add_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        comment = Comment(**comment_add_vo.model_dump())
        comment.user_id = user_id
        comment.status = CommentStatusEnum.PASS
        async with transactions.in_transaction():
            await comment.save()
            await self.redis_util.Article.incr_article_comment_count(comment_add_vo.obj_id)
        ret = CommentDTO.model_validate(comment, from_attributes=True)
        asyncio.create_task(self._send_notice(user_id, comment_add_vo))
        return ret

    async def delete(self, comment_id: int):
        """
        根据评论id删除评论
        :param comment_id:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        await Comment.filter(id=comment_id, user_id=user_id).update(status=CommentStatusEnum.DELETE)
        await self.redis_util.Article.incr_article_comment_count(comment_id, -1)

    async def _send_notice(self, user_id: int, comment_add_vo: CommentAddVO):
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
        elif comment_add_vo.obj_type == ObjectTypeEnum.SHARE:
            share = await self.share_dao.get_share(comment_add_vo.obj_id)
            notice_dto.detail.obj_content = share.content
            notice_dto.user_id = share.user_id
            notice_dto.title = "评论了你的分享"
        if comment_add_vo.parent_id == CommonConstant.TOP_LEVEL:
            notice_dto.notice_type = NoticeTypeEnum.COMMENT
        else:
            setting_key = UserSettingsEnum.WHEN_REPLY_MY_COMMENT
            notice_dto.title = "回复了你的评论"
            notice_dto.notice_type = NoticeTypeEnum.REPLY
            parent_comment = await Comment.filter(id=comment_add_vo.parent_id).first()
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
