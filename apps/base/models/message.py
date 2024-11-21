from tortoise import fields

from apps.base.constant.common_constant import CommonConstant
from apps.base.models.base import BaseModel


class Message(BaseModel):
    user_id = fields.BigIntField(description="用户id", default=CommonConstant.TOP_LEVEL)
    avatar = fields.CharField(max_length=300, null=True, description="头像")
    nickname = fields.CharField(max_length=30, null=True, description="昵称")
    email = fields.CharField(max_length=100, null=True, description="联系人邮箱")
    address = fields.CharField(max_length=100, description="地址")
    content = fields.TextField(description="留言内容")
    parent_id = fields.BigIntField(description="父id", default=CommonConstant.TOP_LEVEL)
    reply_user_id = fields.BigIntField(description="回复的评论所属用户id, 便于查询组装结果",
                                       default=CommonConstant.TOP_LEVEL)
    first_level_id = fields.BigIntField(description="第一层级评论id, 方便查询", default=CommonConstant.TOP_LEVEL)

    class Meta:
        table = "t_message"
        table_description = "留言表"
