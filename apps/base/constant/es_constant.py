class BaseESConstant:
    """Elasticsearch 公共索引常量。"""

    ARTICLE_INDEX = "article"
    ARTICLE_INDEX_MAPPING = {
        "properties": {
            "id": {"type": "long"},
            "user_id": {"type": "long"},
            "cover": {"type": "keyword", "index": False},
            "cover_thumb": {"type": "keyword", "index": False},
            "title": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart",
            },
            "content": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart",
            },
            "category_id": {"type": "long"},
            "tag_list": {"type": "long"},
            "is_markdown": {"type": "boolean", "index": False},
            "is_original": {"type": "boolean"},
            "status": {"type": "integer"},
            "create_time": {"type": "date"},
            "update_time": {"type": "date", "index": False},
            "edit_time": {"type": "date", "index": False},
            "view_count": {"type": "long"},
            "like_count": {"type": "long", "index": False},
            "collect_count": {"type": "long", "index": False},
            "comment_count": {"type": "long", "index": False},
            "hot_score": {"type": "double"},
            "user": {
                "properties": {
                    "id": {"type": "long"},
                    "nickname": {"type": "keyword", "index": False},
                    "avatar": {"type": "keyword", "index": False},
                    "address": {"type": "keyword", "index": False},
                    "gender": {"type": "integer", "index": False},
                    "summary": {"type": "keyword", "index": False},
                }
            },
        }
    }
