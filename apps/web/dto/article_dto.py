# @Time    : 2024/8/11 13:33
# @Author  : frank
# @File    : article_dto.py

import datetime
from email.policy import default
from typing import Optional

from pydantic import Field

from apps.base.enum.article import ArticleStatusEnum
from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.user_dto import UserBaseInfoDTO


class ArticleListDTO(BaseDTO):
    id: int
    user_id: int
    title: str
    cover: str
    category_id: int
    tag_list: list[int]
    content: str
    is_markdown: bool
    is_original: bool
    status: ArticleStatusEnum
    create_time: datetime.datetime
    edit_time: Optional[datetime.datetime] = None
    view_count: Optional[int] = Field(default=0)
    like_count: Optional[int] = Field(default=0)
    collect_count: Optional[int] = Field(default=0)
    comment_count: Optional[int] = Field(default=0)
    user: Optional[UserBaseInfoDTO] = None


class ArticleESDTO(BaseDTO):
    _id: int = None
    _index: str = None
    id: int
    user_id: int
    title: str
    cover: str
    category_id: int
    tag_list: list[int]
    content: str
    is_markdown: bool
    is_original: bool
    status: ArticleStatusEnum
    create_time: datetime.datetime
    edit_time: Optional[datetime.datetime] = None
    view_count: Optional[int] = Field(default=0)
    like_count: Optional[int] = Field(default=0)
    collect_count: Optional[int] = Field(default=0)
    comment_count: Optional[int] = Field(default=0)
    user: Optional[UserBaseInfoDTO] = None

class ArticleBaseInfoDTO(BaseDTO):
    id: int
    user_id: int
    title: str
    cover: str
    create_time: datetime.datetime


class ArticleDTO(BaseDTO):
    id: int
    user_id: int
    title: str
    cover: str
    category_id: int
    tag_list: list[int]
    attach_list: Optional[list]
    content: str
    is_markdown: bool
    is_original: bool
    original_url: Optional[str]
    status: ArticleStatusEnum
    create_time: datetime.datetime
    update_time: datetime.datetime
    edit_time: Optional[datetime.datetime] = Field(default=None)
    view_count: Optional[int] = Field(default=0)
    like_count: Optional[int] = Field(default=0)
    collect_count: Optional[int] = Field(default=0)
    comment_count: Optional[int] = Field(default=0)
    user: Optional[UserBaseInfoDTO] = None
    newest_article_list: list[ArticleBaseInfoDTO] = []
    last_article: Optional[ArticleBaseInfoDTO] = None
    next_article: Optional[ArticleBaseInfoDTO] = None
