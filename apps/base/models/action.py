from tortoise import fields

from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.models.base import BaseModel


class Action(BaseModel):
    """
    动作记录，如点赞、喜欢、收藏、关注
    """
    user_id = fields.BigIntField(description="用户id")
    obj_id = fields.BigIntField(description="对象id")
    obj_type = fields.IntEnumField(ObjectTypeEnum, description="对象类型 1:文章 2:评论 3:用户")
    action_type = fields.IntEnumField(ActionTypeEnum, description="动作类型 1:点赞 2:喜欢 3:收藏 4:关注")
    status = fields.BooleanField(default=False, description="状态 true:已XX false:未XX")

    class Meta:
        table = "t_action"
        table_description = "行为表"


class ActionCount(BaseModel):
    """
    动作统计
    """
    obj_id = fields.BigIntField(description="对象id")
    obj_type = fields.IntEnumField(ObjectTypeEnum, description="对象类型 1:文章 2:评论 3:用户")
    action_type = fields.IntEnumField(ActionTypeEnum,
                                      description="动作类型 1:点赞 2:喜欢 3:收藏 4:关注 5:访问量 6:评论")
    count = fields.IntField(default=0, description="统计数量")

    class Meta:
        table = "t_action_count"
        table_description = "行为统计表"
