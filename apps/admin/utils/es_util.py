from elasticsearch import AsyncElasticsearch, helpers

from apps.base.core.depend_inject import Component, RefreshScope, Value


@Component("adminESUtil")
@RefreshScope("es")
class AdminESUtil:
    """后台 Elasticsearch 客户端。"""

    url: str = Value("es.url")

    def __init__(self) -> None:
        """初始化后台 Elasticsearch 客户端。"""
        self.client = AsyncElasticsearch(self.url)
        self.helpers = helpers
