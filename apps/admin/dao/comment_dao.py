from typing import Any

from sqlalchemy import delete, select, update

from apps.admin.dao.base_dao import _paginate
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.action import ObjectTypeEnum
from apps.base.models.article import Article
from apps.base.models.comment import Comment
from apps.base.models.picture import Picture
from apps.base.models.user import User
from apps.base.utils.comment_count_util import sync_picture_comment_count


@Component()
class AdminCommentDao:
    """后台评论数据访问对象。"""

    async def list_comments(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        obj_id: int | None = None,
        obj_type: int | None = None,
        status: int | None = None,
        user_id: int | None = None,
    ) -> tuple[list[Comment], int]:
        """
        分页查询评论。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 评论内容关键词。
        :param obj_id: 对象 ID。
        :param obj_type: 对象类型。
        :param status: 评论状态。
        :param user_id: 用户 ID。
        :return: 评论列表和总数。
        """
        stmt = select(Comment)
        if keyword:
            stmt = stmt.where(Comment.content.ilike(f"%{keyword}%"))
        if obj_id:
            stmt = stmt.where(Comment.obj_id == obj_id)
        if obj_type is not None:
            stmt = stmt.where(Comment.obj_type == obj_type)
        if status is not None:
            stmt = stmt.where(Comment.status == status)
        if user_id:
            stmt = stmt.where(Comment.user_id == user_id)
        return await _paginate(stmt, current, size, Comment.id.desc())

    async def get_comment_by_id(self, comment_id: int) -> Comment | None:
        """
        根据 ID 查询评论。

        :param comment_id: 评论 ID。
        :return: 评论对象。
        """
        return await db.model_first(select(Comment).where(Comment.id == comment_id))

    async def list_comment_users(self, user_ids: list[int]) -> dict[int, User]:
        """
        批量查询评论用户。

        :param user_ids: 用户 ID 列表。
        :return: 用户 ID 到用户对象的映射。
        """
        if not user_ids:
            return {}
        users = await db.model_all(select(User).where(User.id.in_(user_ids)))
        return {user.id: user for user in users}

    async def list_comment_object_contents(self, comments: list[Comment]) -> dict[tuple[int, int], str]:
        """
        批量查询评论对象的展示内容。

        :param comments: 评论列表。
        :return: 对象类型和对象 ID 到展示内容的映射。
        """
        object_ids: dict[int, set[int]] = {}
        for comment in comments:
            object_ids.setdefault(comment.obj_type, set()).add(comment.obj_id)

        contents: dict[tuple[int, int], str] = {}
        article_ids = object_ids.get(ObjectTypeEnum.ARTICLE, set())
        if article_ids:
            articles = await db.model_all(select(Article).where(Article.id.in_(article_ids)))
            contents.update({(ObjectTypeEnum.ARTICLE, article.id): article.title for article in articles})

        comment_ids = object_ids.get(ObjectTypeEnum.COMMENT, set())
        if comment_ids:
            target_comments = await db.model_all(select(Comment).where(Comment.id.in_(comment_ids)))
            contents.update({(ObjectTypeEnum.COMMENT, comment.id): comment.content for comment in target_comments})

        user_ids = object_ids.get(ObjectTypeEnum.USER, set())
        if user_ids:
            users = await db.model_all(select(User).where(User.id.in_(user_ids)))
            contents.update({(ObjectTypeEnum.USER, user.id): user.nickname or user.username for user in users})

        picture_ids = object_ids.get(ObjectTypeEnum.PICTURE, set())
        if picture_ids:
            pictures = await db.model_all(select(Picture).where(Picture.id.in_(picture_ids)))
            contents.update(
                {(ObjectTypeEnum.PICTURE, picture.id): picture.description or picture.url for picture in pictures}
            )
        return contents

    async def list_parent_comment_contents(self, comments: list[Comment]) -> dict[int, str]:
        """
        批量查询父级评论内容。

        :param comments: 评论列表。
        :return: 父评论 ID 到评论内容的映射。
        """
        parent_ids = {comment.parent_id for comment in comments if comment.parent_id}
        if not parent_ids:
            return {}
        parent_comments = await db.model_all(select(Comment).where(Comment.id.in_(parent_ids)))
        return {comment.id: comment.content for comment in parent_comments}

    async def update_comment(self, comment: Comment, data: dict[str, Any]) -> Comment:
        """
        更新评论。

        :param comment: 评论对象。
        :param data: 更新数据。
        :return: 评论对象。
        """
        if not data:
            return comment
        old_status = comment.status
        new_status = data.get("status", old_status)
        for key, value in data.items():
            setattr(comment, key, value)
        async with db.atomic() as session:
            await session.execute(update(Comment).where(Comment.id == comment.id).values(**data))
            await sync_picture_comment_count(session, comment.obj_type, comment.obj_id, old_status, new_status)
        return comment

    async def delete_comment(self, comment_id: int) -> None:
        """
        删除评论。

        :param comment_id: 评论 ID。
        :return: None。
        """
        comment = await db.model_first(select(Comment).where(Comment.id == comment_id))
        if not comment:
            return
        async with db.atomic() as session:
            await session.execute(delete(Comment).where(Comment.id == comment_id))
            await sync_picture_comment_count(session, comment.obj_type, comment.obj_id, comment.status, None)
