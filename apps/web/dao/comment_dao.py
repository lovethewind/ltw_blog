# @Time    : 2024/10/22 17:05
# @Author  : frank
# @File    : comment_dao.py
from collections.abc import Iterable

from apps.base.core.depend_inject import Component
from apps.base.enum.action import ObjectTypeEnum
from apps.base.models.comment import Comment


@Component()
class CommentDao:

    async def get_comment(self, comment_id: int):
        return await Comment.filter(id=comment_id).first()

    async def clear_comment(self, obj_ids: Iterable[int], obj_type: ObjectTypeEnum):
        """
        清除对象相关评论
        :param obj_ids:
        :param obj_type:
        :return:
        """
        await Comment.filter(obj_id__in=obj_ids, obj_type=obj_type).delete()
