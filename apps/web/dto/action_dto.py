# @Time    : 2024/9/12 16:02
# @Author  : frank
# @File    : action_dto.py
from datetime import datetime

from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.user_dto import UserSimpleInfoDTO


class ActionDTO(BaseDTO):
    id: int
    action_type: ActionTypeEnum
    obj_id: int
    obj_type: ObjectTypeEnum

class UserFollowInfoDTO(BaseDTO):
    id: int
    nickname: str
    avatar: str
    address: str
    summary: str
    # (登录用户)是否关注该用户
    is_followed: bool = False
    # 该用户是否我(登录用户)的粉丝
    is_my_fans: bool = False

class BlckListDTO(BaseDTO):
    id: int
    obj_id: int
    obj_type: ObjectTypeEnum
    user_profile: UserSimpleInfoDTO = None
    update_time: datetime