# @Time    : 2024/10/14 14:31
# @Author  : frank
# @File    : es.py
import json
from datetime import datetime, timedelta

from redis.asyncio import Redis

from apps.base.constant.redis_constant import RedisConstant
from apps.base.utils.page_util import PageResult
from apps.web.vo.search_vo import ArticleSearchVO
from apps.web.dto.article_dto import ArticleListDTO, ArticleBaseInfoDTO


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
        if not await self._redis.exists(key):
            await self._redis.expire(key, timedelta(days=1))
        await self._redis.zincrby(key, 1, word)

    async def get_daily_hot_words_list(self) -> list[str]:
        """
        获取每日热搜前10个关键字
        :return:
        """
        key = f"{RedisConstant.HOT_KEYWORDS_SEARCH_KEY}:{datetime.today().date()}"
        return await self._redis.zrevrange(key, 0, 10)

    async def get_recommend_article_list(self, article_id: int) -> PageResult[ArticleListDTO]:
        """
        获取相关文章的推荐文章
        :param article_id:
        :return:
        """
        key = f"{RedisConstant.RECOMMEND_ARTICLE_SEARCH_KEY}:{article_id}"
        ret = await self._redis.get(key)
        if ret:
            ret = PageResult[ArticleBaseInfoDTO](**json.loads(ret))
        return ret

    async def cache_recommend_article_list(self, article_id: int, result: PageResult[ArticleListDTO]):
        """
        缓存相关文章的推荐文章
        :param article_id:
        :param result:
        :return:
        """
        key = f"{RedisConstant.RECOMMEND_ARTICLE_SEARCH_KEY}:{article_id}"
        await self._redis.set(key, result.model_dump_json(), timedelta(minutes=30))

    async def cache_article_search_result(self, article_search_vo: ArticleSearchVO, result: PageResult[ArticleListDTO]):
        """
        缓存关键字搜索结果
        :param article_search_vo:
        :param result:
        :return:
        """
        key = f"{RedisConstant.KEYWORDS_SEARCH_ARTICLE_CACHE_KEY}:{article_search_vo.keyword.strip()}:{article_search_vo.current_page}:{article_search_vo.page_size}:{article_search_vo.order_type}"
        await self._redis.set(key, result.model_dump_json(), timedelta(minutes=5))

    async def clear_article_search_result(self):
        """
        清除关键字搜索结果
        :return:
        """
        keywords = await self._redis.keys(f"{RedisConstant.KEYWORDS_SEARCH_ARTICLE_CACHE_KEY}:*")
        if not keywords:
            return
        await self._redis.delete(*keywords)

    async def get_article_search_result(self, article_search_vo: ArticleSearchVO) -> PageResult[ArticleListDTO]:
        """
        获取关键字搜索结果
        :param article_search_vo:
        :return:
        """
        key = f"{RedisConstant.KEYWORDS_SEARCH_ARTICLE_CACHE_KEY}:{article_search_vo.keyword.strip()}:{article_search_vo.current_page}:{article_search_vo.page_size}:{article_search_vo.order_type}"
        ret = await self._redis.get(key)
        if ret:
            ret = PageResult[ArticleListDTO](**json.loads(ret))
        return ret
