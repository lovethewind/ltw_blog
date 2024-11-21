from tortoise import fields

from apps.base.constant.common_constant import CommonConstant
from apps.base.enum.action import ObjectTypeEnum
from apps.base.enum.comment import CommentStatusEnum
from apps.base.models.base import BaseModel


class Comment(BaseModel):
    """
    评论功能
    """
    user_id = fields.BigIntField(description="评论用户id")
    obj_id = fields.BigIntField(description="评论对象id")
    obj_type = fields.IntEnumField(ObjectTypeEnum, default=ObjectTypeEnum.ARTICLE,
                                   description="评论对象类型 1:文章 2:分享")
    parent_id = fields.BigIntField(description="父id", default=CommonConstant.TOP_LEVEL)
    reply_user_id = fields.BigIntField(description="回复的评论所属用户id, 便于查询组装结果",
                                       default=CommonConstant.TOP_LEVEL)
    first_level_id = fields.BigIntField(description="第一层级评论id, 方便查询", default=CommonConstant.TOP_LEVEL)
    content = fields.TextField(description="评论内容")
    status = fields.IntEnumField(CommentStatusEnum, description="评论状态 1:通过 2:审核中 3:已删除",
                                 default=CommentStatusEnum.PASS)

    class Meta:
        table = "t_comment"
        table_description = "评论表"
        indexes = [
            (("user_id", "obj_type", "status"), "idx_user_together"),
            (("obj_id", "obj_type", "status"), "idx_obj_together"),
        ]
