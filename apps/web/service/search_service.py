# @Time    : 2024/10/14 14:07
# @Author  : frank
# @File    : search_service.py
import asyncio

from tortoise.expressions import Q

from apps.base.core.depend_inject import Autowired, Component
from apps.base.models.article import Article
from apps.base.models.user import User
from apps.base.utils.redis_util import RedisUtil
from apps.web.core.es.constant.es_constant import ESConstant
from apps.web.core.es.utils.es_util import ESUtil
from apps.web.core.es.utils.html_util import HtmlUtil
from apps.web.dao.article_dao import ArticleDao
from apps.web.dto.article_dto import ArticleBaseInfoDTO, ArticleListDTO
from apps.web.dto.user_dto import UserCommonInfoDTO
from apps.web.vo.search_vo import ArticleRecommendVO, ArticleSearchVO, UserSearchVO


@Component()
class SearchService:
    redis_util: RedisUtil = Autowired()
    es_util: ESUtil = Autowired()
    article_dao: ArticleDao = Autowired()

    async def get_es_article_list(self, article_search_vo: ArticleSearchVO) -> dict:
        """
        ES根据关键词查找文章
        :param article_search_vo:
        :return:
        """
        page = await self.redis_util.ES.get_article_search_result(article_search_vo)
        if page:
            return page
        resp = await self.es_util.client.search(
            index=ESConstant.ARTICLE_INDEX, **ESConstant.get_article_search_dsl(article_search_vo)
        )
        total, records = 0, []
        if resp["hits"]["hits"]:
            total = resp["hits"]["total"]["value"]
            await self.redis_util.ES.save_daily_hot_word(article_search_vo.keyword.strip())
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
        return page

    async def get_user_list(self, search_vo: UserSearchVO) -> dict:
        """
        搜索用户
        :param search_vo:
        :return:
        """
        q = User.filter()
        if search_vo.keyword.isdigit():
            q = q.filter(Q(uid=int(search_vo.keyword)) | Q(nickname__icontains=search_vo.keyword))
        else:
            q = q.filter(nickname__icontains=search_vo.keyword)
        current = search_vo.current_page
        size = search_vo.page_size
        total, users = await asyncio.gather(q.count(), q.page(current, size).all())
        for user in users:
            user.article_count = await self.article_dao.get_user_article_count(user.id)
            user.fans_count = await self.redis_util.Action.get_fans_count(user.id)
        return {"total": total, "records": UserCommonInfoDTO.bulk_model_validate(users)}

    async def get_daily_hot_words_list(self):
        """
        获取每日热搜前10个关键字
        :return:
        """
        ret = await self.redis_util.ES.get_daily_hot_words_list()
        return ret

    async def get_recommend_article_list(self, article_recommend_vo: ArticleRecommendVO) -> dict:
        """
        获取相关文章的推荐文章
        :param article_recommend_vo:
        :return:
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
        初始化article索引
        :return:
        """
        await self.es_util.client.indices.delete(index=ESConstant.ARTICLE_INDEX, ignore_unavailable=True)
        await self.es_util.client.indices.create(
            index=ESConstant.ARTICLE_INDEX, mappings=ESConstant.ARTICLE_INDEX_MAPPING
        )
        await self.redis_util.ES.clear_article_search_result()
        q = Article.filter(is_deleted=False)
        size = 500
        total = await q.count()
        pages = (total + size - 1) // size
        for i in range(pages):
            articles = await q.page(i + 1, size).all()
            records = await self.article_dao.get_article_detail_by_ids(articles=articles)
            ret = []
            for record in records:
                record.content = HtmlUtil.remove_html_tags(record.content)
                record_dict = record.model_dump()
                record_dict["_index"] = ESConstant.ARTICLE_INDEX
                record_dict["_id"] = record.id
                ret.append(record_dict)
            await self.es_util.helpers.async_bulk(self.es_util.client, ret)
