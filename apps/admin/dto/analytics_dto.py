from pydantic import Field

from apps.admin.dto.base_dto import BaseDTO


class AdminAnalyticsOverviewDTO(BaseDTO):
    """后台分析概览数据。"""

    total_users: int = 0
    today_users: int = 0
    published_articles: int = 0
    pending_articles: int = 0
    total_comments: int = 0
    pending_comments: int = 0
    total_views: int = 0
    total_interactions: int = 0


class AdminAnalyticsTrendDTO(BaseDTO):
    """后台分析每日增长趋势。"""

    date: str
    users: int = 0
    articles: int = 0
    comments: int = 0


class AdminAnalyticsNameValueDTO(BaseDTO):
    """后台分析名称数值数据。"""

    name: str
    value: int


class AdminAnalyticsHotArticleDTO(BaseDTO):
    """后台分析热门文章数据。"""

    id: int
    title: str
    author: str
    views: int = 0
    likes: int = 0
    collects: int = 0
    comments: int = 0


class AdminAnalyticsPendingDTO(BaseDTO):
    """后台分析待处理数据。"""

    articles: int = 0
    comments: int = 0
    pictures: int = 0
    links: int = 0
    banned_users: int = 0
    muted_users: int = 0


class AdminAnalyticsDTO(BaseDTO):
    """后台运营分析数据。"""

    overview: AdminAnalyticsOverviewDTO = Field(default_factory=AdminAnalyticsOverviewDTO)
    trends: list[AdminAnalyticsTrendDTO] = Field(default_factory=list)
    article_statuses: list[AdminAnalyticsNameValueDTO] = Field(default_factory=list)
    categories: list[AdminAnalyticsNameValueDTO] = Field(default_factory=list)
    hot_articles: list[AdminAnalyticsHotArticleDTO] = Field(default_factory=list)
    pending: AdminAnalyticsPendingDTO = Field(default_factory=AdminAnalyticsPendingDTO)


__all__ = [
    "AdminAnalyticsDTO",
    "AdminAnalyticsHotArticleDTO",
    "AdminAnalyticsNameValueDTO",
    "AdminAnalyticsOverviewDTO",
    "AdminAnalyticsPendingDTO",
    "AdminAnalyticsTrendDTO",
]
