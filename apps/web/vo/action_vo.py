# @Time    : 2024/9/12 14:42
# @Author  : frank
# @File    : action_vo.py
from typing import Optional

from pydantic import Field

from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.enum.article import ArticleStatusEnum
from apps.web.vo.article_vo import OrderTypeEnum
from apps.web.vo.base_vo import BaseVO


class ActionQueryVO(BaseVO):
    user_id: Optional[int] = Field(default=None)
    action_type: Optional[ActionTypeEnum] = Field(default=None)
    obj_id: Optional[int] = Field(default=None)
    obj_type: Optional[ObjectTypeEnum] = Field(default=None)


class ActionAddVO(BaseVO):
    action_type: ActionTypeEnum
    obj_id: int
    obj_type: ObjectTypeEnum


class ActionTypeDetailQueryVO(BaseVO):
    """
    具体行为查询需要用到的参数
    """
    keyword: Optional[str] = Field(default=None)
    user_id: Optional[int] = Field(default=None)
    tag_id: Optional[int] = Field(default=None)
    category_id: Optional[int] = Field(default=None)
    order_type: Optional[OrderTypeEnum] = Field(default=OrderTypeEnum.BY_CREATE_TIME)
    status: Optional[ArticleStatusEnum] = Field(default=None)
    is_original: Optional[bool] = Field(default=None)
    date_from: Optional[str] = Field(default=None)
    date_to: Optional[str] = Field(default=None)
