import json
import math
import re
from datetime import datetime

from pydantic import ValidationError

from apps.admin.dao.article_dao import AdminArticleDao
from apps.admin.dao.config_dao import AdminConfigDao
from apps.admin.utils.es_util import AdminESUtil
from apps.admin.utils.redis_util import AdminRedisUtil
from apps.admin.vo.search_analysis_vo import SearchAnalysisConfigVO, SearchAnalysisPreviewVO
from apps.base.constant.es_constant import BaseESConstant
from apps.base.core.depend_inject import Autowired, Component
from apps.base.dto.search_analysis_dto import (
    SearchAnalysisConfigDTO,
    SearchAnalysisPreviewDTO,
    SearchAnalysisStateDTO,
    SearchIndexRebuildDTO,
)


@Component()
class AdminSearchAnalysisService:
    """后台搜索分词配置服务。"""

    DRAFT_KEY = "search.analysis.draft"
    PUBLISHED_KEY = "search.analysis.published"
    HISTORY_KEY = "search.analysis.history"

    config_dao: AdminConfigDao = Autowired()
    article_dao: AdminArticleDao = Autowired()
    es_util: AdminESUtil = Autowired("adminESUtil")
    redis_util: AdminRedisUtil = Autowired("adminRedisUtil")

    async def get_state(self) -> SearchAnalysisStateDTO:
        """
        获取搜索分词配置状态。

        :return: 草稿、已发布配置和历史版本。
        """
        records = await self.config_dao.get_configs_by_names([self.DRAFT_KEY, self.PUBLISHED_KEY, self.HISTORY_KEY])
        published = self._parse_config(getattr(records.get(self.PUBLISHED_KEY), "value", None))
        draft_value = getattr(records.get(self.DRAFT_KEY), "value", None)
        draft = self._parse_config(draft_value) if draft_value else published.model_copy(update={"published_at": None})
        history = self._parse_history(getattr(records.get(self.HISTORY_KEY), "value", None))
        return SearchAnalysisStateDTO(draft=draft, published=published, history=history)

    async def save_draft(self, config_vo: SearchAnalysisConfigVO) -> SearchAnalysisStateDTO:
        """
        保存搜索分词草稿。

        :param config_vo: 搜索分词草稿。
        :return: 更新后的配置状态。
        """
        state = await self.get_state()
        draft = config_vo.to_dto().model_copy(update={"version": state.published.version, "published_at": None})
        await self.config_dao.save_named_configs({self.DRAFT_KEY: (draft.model_dump_json(), "搜索分词配置草稿")})
        return state.model_copy(update={"draft": draft})

    async def publish(self) -> SearchAnalysisStateDTO:
        """
        发布当前搜索分词草稿。

        :return: 发布后的配置状态。
        """
        state = await self.get_state()
        published = state.draft.model_copy(
            update={"version": state.published.version + 1, "published_at": datetime.now()}
        )
        history = [published, *state.history]
        history = history[:3]
        await self.config_dao.save_named_configs(
            {
                self.PUBLISHED_KEY: (published.model_dump_json(), "已发布搜索分词配置"),
                self.HISTORY_KEY: (
                    json.dumps([item.model_dump(mode="json") for item in history], ensure_ascii=False),
                    "搜索分词配置发布历史",
                ),
            }
        )
        return state.model_copy(update={"published": published, "history": history})

    async def preview(self, preview_vo: SearchAnalysisPreviewVO) -> SearchAnalysisPreviewDTO:
        """
        使用当前 ES 搜索分析器预览分词，并模拟草稿停用词过滤。

        :param preview_vo: 分词预览参数。
        :return: 原始 token 和过滤后 token。
        """
        response = await self.es_util.client.indices.analyze(analyzer="ik_smart", text=preview_vo.text)
        tokens = [item["token"] for item in response.get("tokens", [])]
        stop_words = set(SearchAnalysisConfigDTO(stop_words=preview_vo.stop_words).stop_words)
        return SearchAnalysisPreviewDTO(
            tokens=tokens,
            filtered_tokens=[token for token in tokens if token not in stop_words],
        )

    async def rebuild_article_index(self) -> SearchIndexRebuildDTO:
        """
        重建文章搜索索引并原子切换读写别名。

        :return: 新索引名称和写入文档数。
        """
        index_name = f"article_v{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        await self.es_util.client.indices.create(
            index=index_name,
            mappings=BaseESConstant.ARTICLE_INDEX_MAPPING,
        )
        size = 500
        total = await self.article_dao.count_index_articles()
        for current in range(1, math.ceil(total / size) + 1):
            articles = await self.article_dao.list_index_articles(current, size)
            author_map = await self.article_dao.list_article_authors(list({article.user_id for article in articles}))
            actions = [
                self._build_article_index_action(article, index_name, author_map.get(article.user_id))
                for article in articles
            ]
            if actions:
                await self.es_util.helpers.async_bulk(self.es_util.client, actions)
        await self._switch_article_alias(index_name)
        await self.redis_util.clear_search_cache()
        return SearchIndexRebuildDTO(index_name=index_name, document_count=total)

    async def _switch_article_alias(self, index_name: str) -> None:
        """
        将 article 别名切换到新物理索引。

        :param index_name: 新物理索引名称。
        :return: None。
        """
        alias = BaseESConstant.ARTICLE_INDEX
        actions: list[dict[str, dict[str, object]]] = []
        if await self.es_util.client.indices.exists_alias(name=alias):
            aliases = await self.es_util.client.indices.get_alias(name=alias)
            actions.extend({"remove": {"index": old_index, "alias": alias}} for old_index in aliases)
        elif await self.es_util.client.indices.exists(index=alias):
            actions.append({"remove_index": {"index": alias}})
        actions.append({"add": {"index": index_name, "alias": alias, "is_write_index": True}})
        await self.es_util.client.indices.update_aliases(actions=actions)

    @staticmethod
    def _build_article_index_action(article: object, index_name: str, user: object | None) -> dict[str, object]:
        """
        构造文章批量索引动作。

        :param article: 文章模型。
        :param index_name: 目标物理索引名称。
        :param user: 文章作者模型。
        :return: Elasticsearch 批量写入动作。
        """
        content = re.sub(r"<[^>]+>", "", str(getattr(article, "content", "")).replace("\n", " "))
        action = {
            "_index": index_name,
            "_id": getattr(article, "id"),
            "id": getattr(article, "id"),
            "user_id": getattr(article, "user_id"),
            "title": getattr(article, "title"),
            "cover": getattr(article, "cover"),
            "cover_thumb": getattr(article, "cover_thumb", ""),
            "category_id": getattr(article, "category_id"),
            "tag_list": getattr(article, "tag_list", []),
            "content": content,
            "is_markdown": getattr(article, "is_markdown", False),
            "is_original": getattr(article, "is_original"),
            "status": getattr(article, "status"),
            "create_time": getattr(article, "create_time"),
            "update_time": getattr(article, "update_time"),
            "edit_time": getattr(article, "edit_time", None),
            "view_count": 0,
            "like_count": 0,
            "collect_count": 0,
            "comment_count": 0,
            "hot_score": float(getattr(article, "hot_score", 0) or 0),
        }
        if user:
            action["user"] = {
                "id": getattr(user, "id"),
                "nickname": getattr(user, "nickname", None),
                "avatar": getattr(user, "avatar", None),
                "address": getattr(user, "address", None),
                "gender": getattr(user, "gender", None),
                "summary": getattr(user, "summary", None),
            }
        return action

    @staticmethod
    def _parse_config(value: str | None) -> SearchAnalysisConfigDTO:
        """
        解析单个搜索配置，异常或空值回退默认配置。

        :param value: 配置 JSON。
        :return: 搜索配置 DTO。
        """
        if not value:
            return SearchAnalysisConfigDTO()
        try:
            return SearchAnalysisConfigDTO.model_validate_json(value)
        except ValidationError:
            return SearchAnalysisConfigDTO()

    @staticmethod
    def _parse_history(value: str | None) -> list[SearchAnalysisConfigDTO]:
        """
        解析搜索配置历史版本。

        :param value: 历史版本 JSON。
        :return: 有效历史配置列表。
        """
        if not value:
            return []
        try:
            data = json.loads(value)
            return [SearchAnalysisConfigDTO.model_validate(item) for item in data[:10]]
        except json.JSONDecodeError, TypeError, ValidationError:
            return []
