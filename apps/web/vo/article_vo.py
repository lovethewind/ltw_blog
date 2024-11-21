from enum import IntEnum
from typing import Optional

from fastapi import Form
from pydantic import Field

from apps.base.enum.article import ArticleStatusEnum
from apps.base.utils.ip_util import IpUtil
from apps.web.core.context_vars import ContextVars
from apps.web.vo.base_vo import BaseVO


class OrderTypeEnum(IntEnum):
    BY_CREATE_TIME = 1
    BY_VIEW_COUNT = 2
    BY_RECOMMEND = 3
    BY_CREATE_TIME_ASC = 4


class ArticleTestVO(BaseVO):
    user_id: int = Form()
    title: str = Form()
    is_original: bool = Form()
    original_url: Optional[str] = Form(default=None)

    class Config:
        data_to_model = True


class ArticleQueryVO(BaseVO):
    keyword: Optional[str] = Field(default=None)
    user_id: Optional[int] = Field(default=None)
    tag_id: Optional[int] = Field(default=None)
    category_id: Optional[int] = Field(default=None)
    order_type: Optional[OrderTypeEnum] = Field(default=OrderTypeEnum.BY_CREATE_TIME)
    status: Optional[ArticleStatusEnum] = Field(default=None)
    is_original: Optional[bool] = Field(default=None)
    date_from: Optional[str] = Field(default=None)
    date_to: Optional[str] = Field(default=None)


class ArticleVO(BaseVO):
    title: str = Field(min_length=1, max_length=100)
    cover: Optional[str] = Field(default=None, max_length=512)
    category_id: int
    tag_list: Optional[list[int]] = Field(default=[])
    attach_list: Optional[list[dict]] = Field(default=[])
    content: str = Field(min_length=1)
    is_markdown: bool
    is_original: bool
    original_url: Optional[str] = Field(default="", max_length=512)
    status: ArticleStatusEnum

    def biz_key(self) -> str:
        user_id = ContextVars.token_user_id.get()
        return f"{user_id}_{self.title}"


class ArticleUpdateVO(BaseVO):
    id: int
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    cover: Optional[str] = Field(default=None, max_length=512)
    category_id: Optional[int] = Field(default=None)
    tag_list: Optional[list[int]] = Field(default=None)
    attach_list: Optional[list[dict]] = Field(default=None)
    content: Optional[str] = Field(default=None, min_length=1)
    is_markdown: Optional[bool] = Field(default=None)
    is_original: Optional[bool] = Field(default=None)
    original_url: Optional[str] = Field(default=None, max_length=512)
    status: Optional[ArticleStatusEnum] = Field(default=None)


class ArticleAddViewCountVO(BaseVO):
    article_id: int

    @property
    def biz_key(self) -> str:
        request = ContextVars.request.get()
        ip_address = IpUtil.get_ip_address(request)
        return f"article_view_count:{self.article_id}:{ip_address}"