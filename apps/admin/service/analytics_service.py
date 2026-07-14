import asyncio
from datetime import date, datetime, time, timedelta

from apps.admin.dao.analytics_dao import AdminAnalyticsDao
from apps.admin.dto.analytics_dto import (
    AdminAnalyticsDTO,
    AdminAnalyticsHotArticleDTO,
    AdminAnalyticsNameValueDTO,
    AdminAnalyticsOverviewDTO,
    AdminAnalyticsPendingDTO,
    AdminAnalyticsTrendDTO,
)
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.article import ArticleStatusEnum


@Component()
class AdminAnalyticsService:
    """后台运营分析服务。"""

    admin_analytics_dao: AdminAnalyticsDao = Autowired()

    async def get_analytics(self) -> AdminAnalyticsDTO:
        """
        获取后台运营分析数据。

        :return: 后台运营分析数据。
        """
        today = date.today()
        today_start = datetime.combine(today, time.min)
        start_date = today - timedelta(days=29)
        start_time = datetime.combine(start_date, time.min)
        overview, trend_rows, status_rows, category_rows, hot_articles, pending = await asyncio.gather(
            self.admin_analytics_dao.get_overview(today_start),
            self.admin_analytics_dao.list_growth_trends(start_time),
            self.admin_analytics_dao.list_article_status_counts(),
            self.admin_analytics_dao.list_category_counts(),
            self.admin_analytics_dao.list_hot_articles(),
            self.admin_analytics_dao.get_pending_counts(datetime.now()),
        )
        return AdminAnalyticsDTO(
            overview=AdminAnalyticsOverviewDTO.model_validate(overview),
            trends=self._build_trends(start_date, trend_rows),
            article_statuses=self._build_article_statuses(status_rows),
            categories=[AdminAnalyticsNameValueDTO(name=name, value=value) for name, value in category_rows],
            hot_articles=AdminAnalyticsHotArticleDTO.bulk_model_validate(hot_articles),
            pending=AdminAnalyticsPendingDTO.model_validate(pending),
        )

    @staticmethod
    def _build_trends(
        start_date: date,
        trend_rows: dict[str, list[tuple[date, int]]],
    ) -> list[AdminAnalyticsTrendDTO]:
        """
        补齐连续三十天的增长趋势。

        :param start_date: 统计开始日期。
        :param trend_rows: 各类型每日增长数据。
        :return: 连续日期增长趋势。
        """
        trend_maps = {key: {day: count for day, count in rows} for key, rows in trend_rows.items()}
        return [
            AdminAnalyticsTrendDTO(
                date=(day := start_date + timedelta(days=index)).isoformat(),
                users=trend_maps["users"].get(day, 0),
                articles=trend_maps["articles"].get(day, 0),
                comments=trend_maps["comments"].get(day, 0),
            )
            for index in range(30)
        ]

    @staticmethod
    def _build_article_statuses(status_rows: list[tuple[int, int]]) -> list[AdminAnalyticsNameValueDTO]:
        """
        转换文章状态统计数据。

        :param status_rows: 文章状态与数量列表。
        :return: 带中文名称的文章状态分布。
        """
        status_names = {
            ArticleStatusEnum.DRAFT: "草稿",
            ArticleStatusEnum.PUBLISHED: "已发布",
            ArticleStatusEnum.CHECKING: "待审核",
            ArticleStatusEnum.DELETED: "回收站",
        }
        status_counts = {ArticleStatusEnum(status): count for status, count in status_rows}
        return [
            AdminAnalyticsNameValueDTO(name=name, value=status_counts.get(status, 0))
            for status, name in status_names.items()
        ]
