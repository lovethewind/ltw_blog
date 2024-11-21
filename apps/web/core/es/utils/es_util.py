# @Time    : 2024/10/15 11:04
# @Author  : frank
# @File    : es_util.py
from elasticsearch import AsyncElasticsearch, helpers

from apps.base.core.depend_inject import Component, RefreshScope, Value


@Component()
@RefreshScope("es")
class ESUtil:
    url: str = Value("es.url")

    def __init__(self):
        self.client = AsyncElasticsearch(self.url)
        self.helpers = helpers
