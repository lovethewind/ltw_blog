import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field

from apps.base.dto.base_dto import BaseDTO
from apps.base.dto.user_dto import UserBaseInfoDTO
from apps.base.enum.article import ArticleStatusEnum


class ArticleListDTO(BaseDTO):
    """
    文章列表 DTO。
    """

    id: int
    user_id: int
    title: str
    cover: str
    cover_thumb: str = ""
    category_id: int
    tag_list: list[int]
    content: str
    is_markdown: bool
    is_original: bool
    status: ArticleStatusEnum
    create_time: datetime.datetime
    collect_time: Optional[datetime.datetime] = Field(default=None)
    edit_time: Optional[datetime.datetime] = None
    view_count: Optional[int] = Field(default=0)
    like_count: Optional[int] = Field(default=0)
    collect_count: Optional[int] = Field(default=0)
    comment_count: Optional[int] = Field(default=0)
    hot_score: Decimal = Decimal(0)
    user: Optional[UserBaseInfoDTO] = None


class ArticleBaseInfoDTO(BaseDTO):
    """
    文章基础信息 DTO。
    """

    id: int
    user_id: int
    title: str
    cover: str
    cover_thumb: str = ""
    create_time: datetime.datetime
