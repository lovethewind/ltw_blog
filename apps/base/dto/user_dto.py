from typing import Optional

from apps.base.dto.base_dto import BaseDTO
from apps.base.enum.user import GenderEnum


class UserBaseInfoDTO(BaseDTO):
    """
    用户基础公开信息 DTO。
    """

    id: Optional[int] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[GenderEnum] = None
    summary: Optional[str] = None
