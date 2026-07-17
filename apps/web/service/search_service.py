import asyncio
import logging
import re
import unicodedata

from sqlalchemy import func, or_, select

from apps.base.core.depend_inject import Autowired, Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.article import Article
from apps.base.models.user import User
from apps.web.core.es.constant.es_constant import ESConstant
from apps.web.core.es.utils.es_util import ESUtil
from apps.web.core.es.utils.html_util import HtmlUtil
from apps.web.dao.article_dao import ArticleDao
from apps.web.dto.article_dto import ArticleBaseInfoDTO, ArticleListDTO
from apps.web.dto.user_dto import UserCommonInfoDTO
from apps.web.service.config_service import ConfigService
from apps.web.utils.redis_util import WebRedisUtil
from apps.web.vo.search_vo import ArticleRecommendVO, ArticleSearchVO, UserSearchVO

logger = logging.getLogger(__name__)


@Component()
class SearchService:
    HOT_SEARCH_STOP_WORDS = frozenset({"一个", "什么", "如何", "怎么", "这个", "那个"})

    redis_util: WebRedisUtil = Autowired()
    es_util: ESUtil = Autowired()
    article_dao: ArticleDao = Autowired()
    config_service: ConfigService = Autowired()

    async def get_es_article_list(self, article_search_vo: ArticleSearchVO) -> dict:
        """
        ES 根据关键词查找文章。

        :param article_search_vo: 文章搜索参数。
        :return: 文章分页结果。
        """
        page = await self.redis_util.ES.get_article_search_result(article_search_vo)
        if page:
            await self._record_hot_search(article_search_vo, page.get("total", 0))
            await self._refresh_article_metrics(page.get("records", []))
            return page
        resp = await self.es_util.client.search(
            index=ESConstant.ARTICLE_INDEX, **ESConstant.get_article_search_dsl(article_search_vo)
        )
        total, records = 0, []
        if resp["hits"]["hits"]:
            total = resp["hits"]["total"]["value"]
            for item in resp["hits"]["hits"]:
                record = item["_source"]
                highlight_title = item["highlight"].get("title")
                highlight_content = item["highlight"].get("content")
                if highlight_title:
                    record["title"] = "...".join(highlight_title)
                if highlight_content:
                    record["content"] = "...".join(highlight_content)
                else:
                    record["content"] = record["content"][:100]
                records.append(ArticleListDTO.model_validate(record))
        page = {"total": total, "records": records}
        await self.redis_util.ES.cache_article_search_result(article_search_vo, page)
        await self._record_hot_search(article_search_vo, total)
        await self._refresh_article_metrics(records)
        return page

    async def _refresh_article_metrics(self, records: list[ArticleListDTO]) -> None:
        """
        使用 Redis 中的实时计数补全 ES 搜索结果。

        :param records: 当前页文章记录。
        :return: None。
        """

        async def refresh_record(record: ArticleListDTO) -> None:
            metric_names = ("view_count", "like_count", "collect_count", "comment_count")
            metrics = await asyncio.gather(
                self.redis_util.Article.get_article_view_count(record.id),
                self.redis_util.Article.get_article_like_count(record.id),
                self.redis_util.Article.get_article_collect_count(record.id),
                self.redis_util.Article.get_article_comment_count(record.id),
                return_exceptions=True,
            )
            for metric_name, metric in zip(metric_names, metrics):
                if isinstance(metric, BaseException):
                    logger.warning("读取文章[%s]实时指标[%s]失败: %s", record.id, metric_name, metric)
                    continue
                setattr(record, metric_name, metric)

        await asyncio.gather(*(refresh_record(record) for record in records))

    @classmethod
    def _normalize_hot_search(cls, keyword: str, stop_words: set[str] | None = None) -> str | None:
        """
        规范化可用于热搜统计的完整搜索短语。

        :param keyword: 用户提交的搜索内容。
        :param stop_words: 动态热搜停用词。
        :return: 规范化后的搜索短语；无效内容返回 None。
        """
        normalized_keyword = unicodedata.normalize("NFKC", keyword)
        normalized_keyword = re.sub(r"\s+", " ", normalized_keyword).strip().casefold()
        if not 2 <= len(normalized_keyword) <= 30:
            return None
        normalized_stop_words = cls.HOT_SEARCH_STOP_WORDS if stop_words is None else stop_words
        if normalized_keyword.isdecimal() or normalized_keyword in normalized_stop_words:
            return None
        if not any(character.isalnum() for character in normalized_keyword):
            return None
        return normalized_keyword

    async def _record_hot_search(self, article_search_vo: ArticleSearchVO, total: int) -> None:
        """
        记录第一页且有结果的文章搜索短语，统计失败不影响正常搜索。

        :param article_search_vo: 文章搜索参数。
        :param total: 搜索结果总数。
        :return: None。
        """
        if article_search_vo.current_page != 1 or total <= 0:
            return
        try:
            config = await self.config_service.get_published_search_analysis()
            stop_words = {
                unicodedata.normalize("NFKC", word).strip().casefold() for word in config.hot_search_stop_words
            }
        except Exception:
            logger.warning("读取热搜停用词失败，使用默认配置", exc_info=True)
            stop_words = set(self.HOT_SEARCH_STOP_WORDS)
        keyword = self._normalize_hot_search(article_search_vo.keyword, stop_words)
        if not keyword:
            return
        try:
            await self.redis_util.ES.save_daily_hot_word(keyword)
        except Exception:
            logger.warning("记录热搜短语失败: %s", keyword, exc_info=True)

    async def get_user_list(self, search_vo: UserSearchVO) -> dict:
        """
        搜索用户。

        :param search_vo: 用户搜索参数。
        :return: 用户分页结果。
        """
        stmt = select(User)
        if search_vo.keyword.isdigit():
            stmt = stmt.where(or_(User.uid == int(search_vo.keyword), User.nickname.ilike(f"%{search_vo.keyword}%")))
        else:
            stmt = stmt.where(User.nickname.ilike(f"%{search_vo.keyword}%"))
        current = search_vo.current_page
        size = search_vo.page_size
        offset, limit = db.page(current, size)
        total_stmt = select(func.count()).select_from(stmt.subquery())
        user_stmt = stmt.order_by(User.id.desc()).offset(offset).limit(limit)
        total, users = await asyncio.gather(
            db.scalar(total_stmt),
            db.model_all(user_stmt),
        )
        for user in users:
            user.article_count = await self.article_dao.get_user_article_count(user.id)
            user.fans_count = await self.redis_util.Action.get_fans_count(user.id)
        return {"total": total, "records": UserCommonInfoDTO.bulk_model_validate(users)}

    async def get_daily_hot_words_list(self):
        """
        获取每日热搜前 10 个关键字。

        :return: 热搜关键词列表。
        """
        ret = await self.redis_util.ES.get_daily_hot_words_list()
        return ret

    async def get_recommend_article_list(self, article_recommend_vo: ArticleRecommendVO) -> dict:
        """
        获取相关文章的推荐文章。

        :param article_recommend_vo: 推荐文章查询参数。
        :return: 推荐文章分页结果。
        """
        page = await self.redis_util.ES.get_recommend_article_list(article_recommend_vo.article_id)
        if page:
            return page
        resp = await self.es_util.client.search(
            index=ESConstant.ARTICLE_INDEX, **ESConstant.get_recommend_article_dsl(article_recommend_vo)
        )
        total, records = 0, []
        if resp["hits"]["hits"]:
            total = resp["hits"]["total"]["value"]
            for item in resp["hits"]["hits"]:
                record = item["_source"]
                records.append(ArticleBaseInfoDTO.model_validate(record))
        page = {"total": total, "records": records}
        await self.redis_util.ES.cache_recommend_article_list(article_recommend_vo.article_id, page)
        return page

    async def init_article_index(self) -> None:
        """
        初始化 article 索引。

        :return: None。
        """
        await self.es_util.client.indices.delete(index=ESConstant.ARTICLE_INDEX, ignore_unavailable=True)
        await self.es_util.client.indices.create(
            index=ESConstant.ARTICLE_INDEX, mappings=ESConstant.ARTICLE_INDEX_MAPPING
        )
        await self.redis_util.ES.clear_article_search_result()
        stmt = select(Article).where(Article.is_deleted.is_(False))
        size = 500
        total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
        pages = (total + size - 1) // size
        for i in range(pages):
            offset, limit = db.page(i + 1, size)
            articles = await db.model_all(stmt.order_by(Article.id.desc()).offset(offset).limit(limit))
            records = await self.article_dao.get_article_detail_by_ids(articles=articles)
            ret = []
            for record in records:
                record.content = HtmlUtil.remove_html_tags(record.content)
                record_dict = record.model_dump()
                record_dict["hot_score"] = float(record_dict.get("hot_score") or 0)
                record_dict["_index"] = ESConstant.ARTICLE_INDEX
                record_dict["_id"] = record.id
                ret.append(record_dict)
            await self.es_util.helpers.async_bulk(self.es_util.client, ret)
