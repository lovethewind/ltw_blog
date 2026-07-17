# @Time    : 2024/10/15 11:09
# @Author  : frank
# @File    : es_constant.py
from apps.base.constant.es_constant import BaseESConstant
from apps.base.enum.article import ArticleStatusEnum
from apps.web.vo.search_vo import ArticleRecommendVO, ArticleSearchVO, OrderTypeEnum


class ESConstant(BaseESConstant):
    """Web 搜索 Elasticsearch 常量与 DSL。"""

    @classmethod
    def get_article_search_dsl(cls, article_search_vo: ArticleSearchVO):
        dsl = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"status": ArticleStatusEnum.PUBLISHED.value}},
                        {"multi_match": {"query": article_search_vo.keyword, "fields": ["title^2", "content"]}},
                    ]
                }
            },
            "from": (article_search_vo.current_page - 1) * article_search_vo.page_size,
            "size": article_search_vo.page_size,
            "highlight": {
                "pre_tags": ["<span class='highlight-keyword'>"],
                "post_tags": ["</span>"],
                "fields": {"content": {}, "title": {}},
            },
        }
        if article_search_vo.order_type == OrderTypeEnum.BY_CREATE_TIME_ASC:
            dsl["sort"] = [{"create_time": {"order": "asc"}}, {"id": {"order": "asc"}}]
        elif article_search_vo.order_type == OrderTypeEnum.BY_CREATE_TIME_DESC:
            dsl["sort"] = [{"create_time": {"order": "desc"}}, {"id": {"order": "desc"}}]
        elif article_search_vo.order_type == OrderTypeEnum.BY_HOT_SCORE:
            dsl["sort"] = [
                {"hot_score": {"missing": "_last", "order": "desc", "unmapped_type": "double"}},
                {"_score": {"order": "desc"}},
                {"id": {"order": "desc"}},
            ]
        else:
            dsl["sort"] = [{"_score": {"order": "desc"}}, {"id": {"order": "desc"}}]
        return dsl

    @classmethod
    def get_recommend_article_dsl(cls, article_recommend_vo: ArticleRecommendVO):
        dsl = {
            "query": {
                "bool": {
                    "must_not": [{"term": {"id": article_recommend_vo.article_id}}],
                    "must": [
                        {"term": {"status": ArticleStatusEnum.PUBLISHED.value}},
                        {"multi_match": {"query": article_recommend_vo.title, "fields": ["title^2", "content"]}},
                    ],
                }
            },
            "from": 0,
            "size": article_recommend_vo.count,
            "sort": [{"id": {"order": "desc"}}],
            "_source": ["id", "title", "cover", "user_id", "create_time"],
        }
        return dsl
