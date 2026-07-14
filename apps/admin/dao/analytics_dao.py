import asyncio
from datetime import date, datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import InstrumentedAttribute, aliased

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.enum.article import ArticleStatusEnum
from apps.base.enum.comment import CommentStatusEnum
from apps.base.enum.common import CheckStatusEnum
from apps.base.enum.user import UserRestrictionTypeEnum
from apps.base.models.action import ActionCount
from apps.base.models.article import Article
from apps.base.models.category import Category
from apps.base.models.comment import Comment
from apps.base.models.link import Link
from apps.base.models.picture import Picture
from apps.base.models.user import User, UserRestriction


@Component()
class AdminAnalyticsDao:
    """后台运营分析数据访问对象。"""

    async def get_overview(self, today_start: datetime) -> dict[str, int]:
        """
        查询运营概览。

        :param today_start: 当天开始时间。
        :return: 运营概览数据。
        """
        stmt = select(
            select(func.count(User.id)).scalar_subquery().label("total_users"),
            select(func.count(User.id)).where(User.register_time >= today_start).scalar_subquery().label("today_users"),
            select(func.count(Article.id))
            .where(Article.status == ArticleStatusEnum.PUBLISHED, Article.is_deleted.is_(False))
            .scalar_subquery()
            .label("published_articles"),
            select(func.count(Article.id))
            .where(Article.status == ArticleStatusEnum.CHECKING, Article.is_deleted.is_(False))
            .scalar_subquery()
            .label("pending_articles"),
            select(func.count(Comment.id))
            .where(Comment.status != CommentStatusEnum.DELETE)
            .scalar_subquery()
            .label("total_comments"),
            select(func.count(Comment.id))
            .where(Comment.status == CommentStatusEnum.CHECKING)
            .scalar_subquery()
            .label("pending_comments"),
            select(func.coalesce(func.sum(ActionCount.count), 0))
            .where(
                ActionCount.obj_type == ObjectTypeEnum.ARTICLE,
                ActionCount.action_type == ActionTypeEnum.VIEW,
            )
            .scalar_subquery()
            .label("total_views"),
            select(func.coalesce(func.sum(ActionCount.count), 0))
            .where(
                ActionCount.obj_type == ObjectTypeEnum.ARTICLE,
                ActionCount.action_type.in_([ActionTypeEnum.LIKE, ActionTypeEnum.COLLECT, ActionTypeEnum.COMMENT]),
            )
            .scalar_subquery()
            .label("total_interactions"),
        )
        row = await db.first(stmt)
        return {key: int(value or 0) for key, value in row._mapping.items()} if row else {}

    async def list_growth_trends(self, start_time: datetime) -> dict[str, list[tuple[date, int]]]:
        """
        查询用户、文章和评论的每日增长量。

        :param start_time: 统计开始时间。
        :return: 按数据类型分组的每日增长量。
        """
        users, articles, comments = await asyncio.gather(
            self._list_daily_counts(User.register_time, start_time),
            self._list_daily_counts(Article.create_time, start_time),
            self._list_daily_counts(Comment.create_time, start_time),
        )
        return {"users": users, "articles": articles, "comments": comments}

    async def _list_daily_counts(
        self,
        date_column: InstrumentedAttribute[datetime],
        start_time: datetime,
    ) -> list[tuple[date, int]]:
        """
        按日期统计指定时间字段的数据量。

        :param date_column: 日期时间字段。
        :param start_time: 统计开始时间。
        :return: 日期与数量列表。
        """
        day_column = func.date(date_column).label("day")
        count_column = func.count().label("count")
        rows = await db.all(
            select(day_column, count_column).where(date_column >= start_time).group_by(day_column).order_by(day_column)
        )
        return [(row.day, int(row.count)) for row in rows]

    async def list_article_status_counts(self) -> list[tuple[int, int]]:
        """
        查询文章状态分布。

        :return: 状态值与文章数量列表。
        """
        rows = await db.all(
            select(Article.status, func.count(Article.id).label("count"))
            .group_by(Article.status)
            .order_by(Article.status)
        )
        return [(int(row.status), int(row.count)) for row in rows]

    async def list_category_counts(self, limit: int = 10) -> list[tuple[str, int]]:
        """
        查询已发布文章的分类分布。

        :param limit: 返回分类数量。
        :return: 分类名称与文章数量列表。
        """
        count_column = func.count(Article.id).label("count")
        rows = await db.all(
            select(Category.name, count_column)
            .join(Article, Article.category_id == Category.id)
            .where(Article.status == ArticleStatusEnum.PUBLISHED, Article.is_deleted.is_(False))
            .group_by(Category.id, Category.name)
            .order_by(count_column.desc(), Category.id.desc())
            .limit(limit)
        )
        return [(str(row.name), int(row.count)) for row in rows]

    async def list_hot_articles(self, limit: int = 10) -> list[dict[str, int | str]]:
        """
        查询热门文章排行。

        :param limit: 返回文章数量。
        :return: 热门文章数据列表。
        """
        view_count = aliased(ActionCount)
        like_count = aliased(ActionCount)
        collect_count = aliased(ActionCount)
        comment_count = aliased(ActionCount)
        views = func.coalesce(view_count.count, 0).label("views")
        rows = await db.all(
            select(
                Article.id,
                Article.title,
                User.nickname.label("author"),
                views,
                func.coalesce(like_count.count, 0).label("likes"),
                func.coalesce(collect_count.count, 0).label("collects"),
                func.coalesce(comment_count.count, 0).label("comments"),
            )
            .join(User, User.id == Article.user_id)
            .outerjoin(
                view_count,
                and_(
                    view_count.obj_id == Article.id,
                    view_count.obj_type == ObjectTypeEnum.ARTICLE,
                    view_count.action_type == ActionTypeEnum.VIEW,
                ),
            )
            .outerjoin(
                like_count,
                and_(
                    like_count.obj_id == Article.id,
                    like_count.obj_type == ObjectTypeEnum.ARTICLE,
                    like_count.action_type == ActionTypeEnum.LIKE,
                ),
            )
            .outerjoin(
                collect_count,
                and_(
                    collect_count.obj_id == Article.id,
                    collect_count.obj_type == ObjectTypeEnum.ARTICLE,
                    collect_count.action_type == ActionTypeEnum.COLLECT,
                ),
            )
            .outerjoin(
                comment_count,
                and_(
                    comment_count.obj_id == Article.id,
                    comment_count.obj_type == ObjectTypeEnum.ARTICLE,
                    comment_count.action_type == ActionTypeEnum.COMMENT,
                ),
            )
            .where(Article.status == ArticleStatusEnum.PUBLISHED, Article.is_deleted.is_(False))
            .order_by(views.desc(), Article.id.desc())
            .limit(limit)
        )
        return [dict(row._mapping) for row in rows]

    async def get_pending_counts(self, now: datetime) -> dict[str, int]:
        """
        查询待处理事项和当前用户限制数量。

        :param now: 当前时间。
        :return: 待处理事项数量。
        """
        active_restriction = and_(
            UserRestriction.is_cancel.is_(False),
            or_(
                UserRestriction.is_forever.is_(True),
                and_(UserRestriction.start_time <= now, UserRestriction.end_time >= now),
            ),
        )
        stmt = select(
            select(func.count(Article.id))
            .where(Article.status == ArticleStatusEnum.CHECKING, Article.is_deleted.is_(False))
            .scalar_subquery()
            .label("articles"),
            select(func.count(Comment.id))
            .where(Comment.status == CommentStatusEnum.CHECKING)
            .scalar_subquery()
            .label("comments"),
            select(func.count(Picture.id))
            .where(Picture.status == CheckStatusEnum.CHECKING)
            .scalar_subquery()
            .label("pictures"),
            select(func.count(Link.id)).where(Link.status == CheckStatusEnum.CHECKING).scalar_subquery().label("links"),
            select(func.count(UserRestriction.id))
            .where(active_restriction, UserRestriction.restrict_type == UserRestrictionTypeEnum.BAN)
            .scalar_subquery()
            .label("banned_users"),
            select(func.count(UserRestriction.id))
            .where(active_restriction, UserRestriction.restrict_type == UserRestrictionTypeEnum.MUTE)
            .scalar_subquery()
            .label("muted_users"),
        )
        row = await db.first(stmt)
        return {key: int(value or 0) for key, value in row._mapping.items()} if row else {}
