# @Time    : 2024/9/3 14:07
# @Author  : frank
# @File    : picture_add_vo.py
from typing import Optional

from pydantic import Field

from apps.base.enum.picture import AlbumTypeEnum
from apps.web.vo.base_vo import BaseVO


class PictureQueryVO(BaseVO):
    user_id: Optional[int] = Field(default=None)
    album_id: Optional[int] = Field(default=None)


class PictureAddVO(BaseVO):
    album_id: int
    url: str
    description: Optional[str] = Field(default="")
    width: int
    height: int
    size: int


class PictureUpdateVO(BaseVO):
    id: int
    album_id: Optional[int] = None
    url: Optional[str] = None
    description: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[int] = None


class PictureAlbumAddVO(BaseVO):
    name: str
    cover: Optional[str] = None
    description: Optional[str] = ""
    album_type: AlbumTypeEnum


class PictureAlbumUpdateVO(BaseVO):
    id: int
    name: Optional[str] = None
    cover: Optional[str] = None
    description: Optional[str] = ""
    album_type: Optional[AlbumTypeEnum] = None
