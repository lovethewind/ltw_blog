# @Time    : 2024/10/15 11:09
# @Author  : frank
# @File    : es_constant.py
from apps.base.enum.article import ArticleStatusEnum
from apps.web.vo.search_vo import ArticleSearchVO, OrderTypeEnum, ArticleRecommendVO


class ESConstant:
    ARTICLE_INDEX = "article"
    ARTICLE_INDEX_MAPPING = {
        "properties": {
            "id": {"type": "long"},
            "user_id": {"type": "long"},
            "cover": {"type": "keyword", "index": False},
            "title": {
                "type": "text",  # 改为text类型以便使用分析器
                "analyzer": "ik_max_word",  # 使用ik_max_word分词器
                "search_analyzer": "ik_smart"  # 搜索时使用ik_smart分词器
            },
            "content": {
                "type": "text",  # 同样改为text类型
                "analyzer": "ik_max_word",  # 使用ik_max_word分词器
                "search_analyzer": "ik_smart",  # 搜索时使用ik_smart分词器
            },
            "category_id": {"type": "long"},
            "tag_list": {"type": "long"},
            "is_original": {"type": "boolean"},
            "status": {"type": "integer"},
            "create_time": {"type": "date"},
            "update_time": {"type": "date", "index": False},
            "view_count": {"type": "long"},
            "like_count": {"type": "long", "index": False},
            "collect_count": {"type": "long", "index": False},
            "comment_count": {"type": "long", "index": False}
        }
    }

    @classmethod
    def get_article_search_dsl(cls, article_search_vo: ArticleSearchVO):
        dsl = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"status": ArticleStatusEnum.PUBLISHED.value}},
                        {"multi_match":
                            {
                                "query": article_search_vo.keyword,
                                "fields": ["title^2", "content"]
                            }
                        }
                    ]
                }
            },
            "from": (article_search_vo.current_page - 1) * article_search_vo.page_size,
            "size": article_search_vo.page_size,
            "highlight": {
                "pre_tags": ["<span class='highlight-keyword'>"],
                "post_tags": ["</span>"],
                "fields": {
                    "content": {},
                    "title": {}
                }
            }
        }
        if article_search_vo.order_type == OrderTypeEnum.BY_CREATE_TIME:
            dsl["sort"] = [{"id": {"order": "asc"}}]
        elif article_search_vo.order_type == OrderTypeEnum.BY_VIEW_COUNT:
            dsl["sort"] = [{"view_count": {"order": "desc"}}]
        else:
            dsl["sort"] = [{"id": {"order": "desc"}}]
        return dsl

    @classmethod
    def get_recommend_article_dsl(cls, article_recommend_vo: ArticleRecommendVO):
        dsl = {
            "query": {
                "bool": {
                    "must_not": [{"term": {"id": article_recommend_vo.article_id}}],
                    "must": [
                        {"term": {"status": ArticleStatusEnum.PUBLISHED.value}},
                        {"multi_match":
                            {
                                "query": article_recommend_vo.title,
                                "fields": ["title^2", "content"]
                            }
                        }
                    ]
                }
            },
            "from": 0,
            "size": article_recommend_vo.count,
            "sort": [{"id": {"order": "desc"}}],
            "_source": ["id", "title", "cover", "user_id", "create_time"]
        }
        return dsl
