from datetime import datetime
from decimal import Decimal

from sqlalchemy import case, select, update

from apps.base.core.depend_inject import logger
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.models.action import ActionCount
from apps.base.models.article import Article

SCORE_QUANT = Decimal("0.000001")


def _calculate_scores(
    article: Article, action_counts: dict[ActionTypeEnum, int], now: datetime
) -> tuple[Decimal, Decimal]:
    """
    根据文章行为计数计算热门分数和推荐分数。

    :param article: 文章对象。
    :param action_counts: 行为类型对应的统计数量。
    :param now: 当前计算时间。
    :return: 热门分数和推荐分数。
    """
    view_count = max(action_counts.get(ActionTypeEnum.VIEW, 0), 0)
    like_count = max(action_counts.get(ActionTypeEnum.LIKE, 0), 0)
    collect_count = max(action_counts.get(ActionTypeEnum.COLLECT, 0), 0)
    comment_count = max(action_counts.get(ActionTypeEnum.COMMENT, 0), 0)
    age_hours = max((now - article.create_time).total_seconds() / 3600, 0)

    interaction_score = view_count * 0.1 + like_count * 3 + collect_count * 5 + comment_count * 4
    hot_score = interaction_score / ((age_hours + 2) ** 1.2)

    quality_score = (like_count * 3 + collect_count * 6 + comment_count * 4) / (view_count + 100) * 1000
    freshness_score = 100 / ((age_hours / 24 + 1) ** 0.5)
    recommend_score = quality_score + freshness_score + article.recommend_weight
    return (
        Decimal(str(hot_score)).quantize(SCORE_QUANT),
        Decimal(str(recommend_score)).quantize(SCORE_QUANT),
    )


async def refresh_article_scores(batch_size: int = 500) -> int:
    """
    分批刷新文章热门分数和推荐分数。

    :param batch_size: 单批处理的文章数量。
    :return: 已刷新分数的文章数量。
    """
    batch_size = max(batch_size, 1)
    last_article_id = 0
    refreshed_count = 0
    now = datetime.now()
    while True:
        articles = list(
            await db.model_all(
                select(Article)
                .where(Article.id > last_article_id, Article.is_deleted.is_(False))
                .order_by(Article.id)
                .limit(batch_size)
            )
        )
        if not articles:
            break

        article_ids = [article.id for article in articles]
        rows = await db.all(
            select(ActionCount.obj_id, ActionCount.action_type, ActionCount.count).where(
                ActionCount.obj_type == ObjectTypeEnum.ARTICLE,
                ActionCount.obj_id.in_(article_ids),
                ActionCount.action_type.in_(
                    [
                        ActionTypeEnum.LIKE,
                        ActionTypeEnum.COLLECT,
                        ActionTypeEnum.VIEW,
                        ActionTypeEnum.COMMENT,
                    ]
                ),
            )
        )
        count_map: dict[int, dict[ActionTypeEnum, int]] = {}
        for obj_id, action_type, count in rows:
            count_map.setdefault(obj_id, {})[ActionTypeEnum(action_type)] = count

        hot_score_map: dict[int, Decimal] = {}
        recommend_score_map: dict[int, Decimal] = {}
        for article in articles:
            hot_score, recommend_score = _calculate_scores(article, count_map.get(article.id, {}), now)
            hot_score_map[article.id] = hot_score
            recommend_score_map[article.id] = recommend_score

        async with db.atomic() as session:
            await session.execute(
                update(Article)
                .where(Article.id.in_(article_ids))
                .values(
                    hot_score=case(hot_score_map, value=Article.id),
                    recommend_score=case(recommend_score_map, value=Article.id),
                )
            )
        refreshed_count += len(articles)
        last_article_id = article_ids[-1]

    logger.info(f"文章排序分数刷新完成，共刷新 {refreshed_count} 篇文章")
    return refreshed_count


if __name__ == "__main__":
    import asyncio

    from apps.scheduler.config.server_config import init_container_config

    init_container_config()
    asyncio.run(refresh_article_scores())
