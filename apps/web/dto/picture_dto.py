# @Time    : 2024/9/3 14:12
# @Author  : frank
# @File    : picture_dto.py
from datetime import datetime
from typing import Optional

from apps.base.enum.common import CheckStatusEnum
from apps.base.enum.picture import AlbumTypeEnum
from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.user_dto import UserBaseInfoDTO


class PictureAlbumDTO(BaseDTO):
    id: int
    name: str
    description: str
    cover: str
    status: CheckStatusEnum
    album_type: AlbumTypeEnum


class PictureDTO(BaseDTO):
    id: int
    user_id: int
    album_id: int
    description: str
    url: str
    size: int
    width: int
    height: int
    status: CheckStatusEnum
    create_time: datetime
    user: Optional[UserBaseInfoDTO] = None
    like_count: int = 0
    has_like: bool = False
