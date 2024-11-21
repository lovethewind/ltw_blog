# @Time    : 2024/9/5 16:49
# @Author  : frank
# @File    : share_vo.py
from typing import Optional

from pydantic import Field

from apps.base.enum.share import ShareTypeEnum
from apps.web.vo.base_vo import BaseVO


class ShareQueryVO(BaseVO):
    share_type: Optional[ShareTypeEnum] = None
    content: Optional[str] = None
    tag: Optional[str] = None
    keyword: Optional[str] = None


class ShareAddVO(BaseVO):
    content: str = Field(min_length=1)
    share_type: ShareTypeEnum
    tag: Optional[list[str]] = None
    detail: Optional[list] = None


class ShareUpdateVO(BaseVO):
    id: int
    content: Optional[str] = None
    share_type: Optional[ShareTypeEnum] = None
    tag: Optional[list[str]] = None
    detail: Optional[list] = None
