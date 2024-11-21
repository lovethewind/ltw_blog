# @Time    : 2024/10/14 14:12
# @Author  : frank
# @File    : search_vo.py
from enum import IntEnum

from apps.web.vo.base_vo import BaseVO


class OrderTypeEnum(IntEnum):
    BY_CREATE_TIME = 1
    BY_CREATE_TIME_ASC = 2
    BY_VIEW_COUNT = 3


class BaseSearchVO(BaseVO):
    keyword: str
    current_page: int
    page_size: int


class ArticleSearchVO(BaseSearchVO):
    order_type: OrderTypeEnum = OrderTypeEnum.BY_CREATE_TIME


class ArticleRecommendVO(BaseVO):
    article_id: int
    title: str
    count: int = 0


class UserSearchVO(BaseSearchVO):
    ...
