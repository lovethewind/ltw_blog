# @Time    : 2024/10/22 17:05
# @Author  : frank
# @File    : comment_dao.py
from collections.abc import Iterable

from tortoise.functions import Count

from apps.base.core.depend_inject import Component
from apps.base.enum.action import ObjectTypeEnum
from apps.base.enum.comment import CommentStatusEnum
from apps.base.models.comment import Comment


@Component()
class CommentDao:

    async def get_comment(self, comment_id: int):
        return await Comment.filter(id=comment_id).first()

    async def get_comment_count(self, obj_id: int, obj_type: ObjectTypeEnum) -> int:
        """
        获取对象已通过的评论数量。
        :param obj_id: 对象 ID。
        :param obj_type: 对象类型。
        :return: 评论数量。
        """
        return await Comment.filter(obj_id=obj_id, obj_type=obj_type, status=CommentStatusEnum.PASS).count()

    async def get_comment_count_map(self, obj_ids: Iterable[int], obj_type: ObjectTypeEnum) -> dict[int, int]:
        """
        批量获取对象已通过的评论数量。
        :param obj_ids: 对象 ID 列表。
        :param obj_type: 对象类型。
        :return: 对象 ID 到评论数量的映射。
        """
        obj_id_list = list(obj_ids)
        if not obj_id_list:
            return {}
        count_info_list = (
            await Comment.filter(obj_id__in=obj_id_list, obj_type=obj_type, status=CommentStatusEnum.PASS)
            .group_by("obj_id")
            .annotate(count=Count("id"))
            .values("obj_id", "count")
        )
        return {item["obj_id"]: item["count"] for item in count_info_list}

    async def clear_comment(self, obj_ids: Iterable[int], obj_type: ObjectTypeEnum):
        """
        清除对象相关评论
        :param obj_ids:
        :param obj_type:
        :return:
        """
        await Comment.filter(obj_id__in=obj_ids, obj_type=obj_type).delete()
