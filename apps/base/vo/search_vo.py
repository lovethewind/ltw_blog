from enum import IntEnum

from apps.base.vo.base_vo import BaseVO


class OrderTypeEnum(IntEnum):
    """
    文章搜索排序类型。
    """

    BY_CREATE_TIME = 1
    BY_CREATE_TIME_ASC = 2
    BY_VIEW_COUNT = 3


class BaseSearchVO(BaseVO):
    """
    通用搜索请求 VO。
    """

    keyword: str
    current_page: int
    page_size: int


class ArticleSearchVO(BaseSearchVO):
    """
    文章搜索请求 VO。
    """

    order_type: OrderTypeEnum = OrderTypeEnum.BY_CREATE_TIME


class ArticleRecommendVO(BaseVO):
    """
    文章推荐请求 VO。
    """

    article_id: int
    title: str
    count: int = 0


class UserSearchVO(BaseSearchVO):
    """
    用户搜索请求 VO。
    """
