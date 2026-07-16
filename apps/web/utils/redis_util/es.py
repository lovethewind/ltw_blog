# @Time    : 2024/10/14 14:31
# @Author  : frank
# @File    : es.py
import json
from datetime import datetime, timedelta
from typing import Any

from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant
from apps.base.dto.article_dto import ArticleBaseInfoDTO, ArticleListDTO
from apps.base.dto.base_dto import BaseDTO
from apps.base.vo.search_vo import ArticleSearchVO


class ESMethod:
    """
    ES相关方法
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def save_daily_hot_word(self, word: str):
        """
        保存每日热搜关键字
        :return:
        """
        key = f"{RedisConstant.HOT_KEYWORDS_SEARCH_KEY}:{datetime.today().date()}"
        await self._redis.zincrby(key, 1, word)
        await self._redis.expire(key, timedelta(days=2))

    async def get_daily_hot_words_list(self) -> list[str]:
        """
        获取每日热搜前10个关键字
        :return:
        """
        key = f"{RedisConstant.HOT_KEYWORDS_SEARCH_KEY}:{datetime.today().date()}"
        return await self._redis.zrevrange(key, 0, 9)

    async def get_recommend_article_list(self, article_id: int) -> dict[str, Any] | None:
        """
        获取相关文章的推荐文章
        :param article_id:
        :return:
        """
        key = f"{RedisConstant.RECOMMEND_ARTICLE_SEARCH_KEY}:{article_id}"
        ret = await self._redis.get(key)
        if ret:
            ret = json.loads(ret)
            ret["records"] = ArticleBaseInfoDTO.bulk_model_validate(ret.get("records", []))
        return ret

    async def cache_recommend_article_list(self, article_id: int, result: dict[str, Any]) -> None:
        """
        缓存相关文章的推荐文章
        :param article_id:
        :param result:
        :return:
        """
        key = f"{RedisConstant.RECOMMEND_ARTICLE_SEARCH_KEY}:{article_id}"
        await self._redis.set(key, self._dump_page_result(result), timedelta(minutes=30))

    async def cache_article_search_result(self, article_search_vo: ArticleSearchVO, result: dict[str, Any]) -> None:
        """
        缓存关键字搜索结果
        :param article_search_vo:
        :param result:
        :return:
        """
        key = f"{RedisConstant.KEYWORDS_SEARCH_ARTICLE_CACHE_KEY}:{article_search_vo.keyword.strip()}:{article_search_vo.current_page}:{article_search_vo.page_size}:{article_search_vo.order_type}"
        await self._redis.set(key, self._dump_page_result(result), timedelta(minutes=5))

    async def clear_article_search_result(self):
        """
        清除关键字搜索结果
        :return:
        """
        keywords = await self._redis.keys(f"{RedisConstant.KEYWORDS_SEARCH_ARTICLE_CACHE_KEY}:*")
        if not keywords:
            return
        await self._redis.delete(*keywords)

    async def get_article_search_result(self, article_search_vo: ArticleSearchVO) -> dict[str, Any] | None:
        """
        获取关键字搜索结果
        :param article_search_vo:
        :return:
        """
        key = f"{RedisConstant.KEYWORDS_SEARCH_ARTICLE_CACHE_KEY}:{article_search_vo.keyword.strip()}:{article_search_vo.current_page}:{article_search_vo.page_size}:{article_search_vo.order_type}"
        ret = await self._redis.get(key)
        if ret:
            ret = json.loads(ret)
            ret["records"] = ArticleListDTO.bulk_model_validate(ret.get("records", []))
        return ret

    @staticmethod
    def _dump_page_result(result: dict[str, Any]) -> str:
        """
        序列化分页结果缓存。

        :param result: 分页结果。
        :return: JSON 字符串。
        """
        records = [
            record.model_dump(mode="json") if isinstance(record, BaseDTO) else record
            for record in result.get("records", [])
        ]
        return json.dumps({"total": result.get("total", 0), "records": records}, ensure_ascii=False)
