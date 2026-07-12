from typing import Any

from sqlalchemy import select

from apps.admin.dao.base_dao import _delete, _paginate, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.comment import Comment


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

    async def update_comment(self, comment: Comment, data: dict[str, Any]) -> Comment:
        """
        更新评论。

        :param comment: 评论对象。
        :param data: 更新数据。
        :return: 评论对象。
        """
        return await _update(comment, data)

    async def delete_comment(self, comment_id: int) -> None:
        """
        删除评论。

        :param comment_id: 评论 ID。
        :return: None。
        """
        await _delete(Comment, comment_id)
