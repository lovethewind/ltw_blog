from datetime import datetime
from decimal import Decimal

from elasticsearch import AsyncElasticsearch, helpers
from sqlalchemy import case, select, update

from apps.base.core.depend_inject import GetValue, logger
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.enum.article import ArticleStatusEnum
from apps.base.models.action import ActionCount
from apps.base.models.article import Article

SCORE_QUANT = Decimal("0.000001")
ARTICLE_INDEX = "article"


async def _sync_article_metrics_to_es(
    client: AsyncElasticsearch,
    article_ids: list[int],
    count_map: dict[int, dict[ActionTypeEnum, int]],
    hot_score_map: dict[int, Decimal],
) -> None:
    """
    将文章行为计数和热门分数批量同步到 ES。

    :param client: Elasticsearch 异步客户端。
    :param article_ids: 待同步文章 ID。
    :param count_map: 文章行为计数映射。
    :param hot_score_map: 文章热门分数映射。
    :return: None。
    """
    documents = await client.mget(
        index=ARTICLE_INDEX, ids=[str(article_id) for article_id in article_ids], source=False
    )
    existing_article_ids = {int(document["_id"]) for document in documents["docs"] if document.get("found")}
    missing_count = len(article_ids) - len(existing_article_ids)
    if missing_count:
        logger.info(f"跳过 {missing_count} 篇尚未写入 ES 的文章指标")
    actions = []
    for article_id in article_ids:
        if article_id not in existing_article_ids:
            continue
        counts = count_map.get(article_id, {})
        actions.append(
            {
                "_op_type": "update",
                "_index": ARTICLE_INDEX,
                "_id": article_id,
                "doc": {
                    "view_count": max(counts.get(ActionTypeEnum.VIEW, 0), 0),
                    "like_count": max(counts.get(ActionTypeEnum.LIKE, 0), 0),
                    "collect_count": max(counts.get(ActionTypeEnum.COLLECT, 0), 0),
                    "comment_count": max(counts.get(ActionTypeEnum.COMMENT, 0), 0),
                    "hot_score": float(hot_score_map[article_id]),
                },
            }
        )
    if not actions:
        return
    success_count, errors = await helpers.async_bulk(
        client,
        actions,
        raise_on_error=False,
        raise_on_exception=False,
    )
    if errors:
        logger.warning(f"文章指标同步 ES 部分失败，成功 {success_count} 条，失败 {len(errors)} 条")


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
    es_client = AsyncElasticsearch(GetValue("es.url"))
    try:
        es_available = bool(await es_client.indices.exists(index=ARTICLE_INDEX))
    except Exception:
        logger.warning("检测文章 ES 索引失败，本轮仅刷新数据库排序分数", exc_info=True)
        es_available = False
    try:
        while True:
            articles = list(
                await db.model_all(
                    select(Article)
                    .where(
                        Article.id > last_article_id,
                        Article.status == ArticleStatusEnum.PUBLISHED,
                        Article.is_deleted.is_(False),
                    )
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
            if es_available:
                try:
                    await _sync_article_metrics_to_es(es_client, article_ids, count_map, hot_score_map)
                except Exception:
                    logger.warning("文章指标同步 ES 失败，本轮继续刷新数据库排序分数", exc_info=True)
            refreshed_count += len(articles)
            last_article_id = article_ids[-1]
    finally:
        await es_client.close()

    logger.info(f"文章排序分数刷新完成，共刷新 {refreshed_count} 篇文章")
    return refreshed_count


if __name__ == "__main__":
    import asyncio

    from apps.scheduler.config.server_config import init_container_config

    init_container_config()
    asyncio.run(refresh_article_scores())
