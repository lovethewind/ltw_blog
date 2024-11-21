# @Time    : 2024/8/28 11:26
# @Author  : frank
# @File    : comment_vo.py
from typing import Optional

from apps.base.constant.common_constant import CommonConstant
from apps.base.enum.action import ObjectTypeEnum
from apps.web.vo.base_vo import BaseVO


class CommentQueryVO(BaseVO):
    obj_id: int
    obj_type: ObjectTypeEnum


class CommentAddVO(BaseVO):
    content: str
    obj_id: int
    obj_type: ObjectTypeEnum
    parent_id: int = CommonConstant.TOP_LEVEL
    reply_user_id: int = CommonConstant.TOP_LEVEL
    first_level_id: int = CommonConstant.TOP_LEVEL
