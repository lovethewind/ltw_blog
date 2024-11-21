# @Time    : 2024/9/12 17:42
# @Author  : frank
# @File    : article_dao.py
import asyncio
from typing import Type

from typing_extensions import TypeVar

from apps.base.core.depend_inject import Component, Autowired
from apps.base.models.article import Article
from apps.base.utils.redis_util import RedisUtil
from apps.web.dao.user_dao import UserDao
from apps.web.dto.article_dto import ArticleListDTO
from apps.web.dto.base_dto import BaseDTO
from apps.web.dto.user_dto import UserBaseInfoDTO
from apps.web.utils.ws_util import manager

T = TypeVar("T", bound=BaseDTO)


@Component()
class ArticleDao:
    user_dao: UserDao = Autowired()
    redis_util: RedisUtil = Autowired()

    async def get_article_detail_by_id(self, article_id: int) -> ArticleListDTO:
        """
        根据文章id获取文章基本信息
        :param article_id: 文章id
        :return: 文章基本信息
        """
        ret = await self.get_article_detail_by_ids([article_id])
        ret = ret[0] if ret else ret
        return ret

    async def get_article_detail_by_ids(self, article_ids: list[int] = None,
                                        articles: list[Article | ArticleListDTO] = None,
                                        clazz: Type[T] = ArticleListDTO) -> list[T]:
        """
        根据文章id/文章获取文章基本信息
        :param article_ids:
        :param articles:
        :param clazz:
        :return:
        """
        if not article_ids and not articles:
            return []
        if not articles:
            articles = await Article.filter(id__in=article_ids)
        ret = []
        for item in articles:
            record = clazz.model_validate(item, from_attributes=True)
            (
                record.view_count,
                record.like_count,
                record.collect_count,
                record.comment_count
            ) = await asyncio.gather(
                self.redis_util.Article.get_article_view_count(record.id),
                self.redis_util.Article.get_article_like_count(record.id),
                self.redis_util.Article.get_article_collect_count(record.id),
                self.redis_util.Article.get_article_comment_count(record.id)
            )
            record.user = await manager.get_user_info(item.user_id, UserBaseInfoDTO)
            ret.append(record)
        return ret

    async def get_article(self, article_id: int):
        return await Article.filter(id=article_id).first()
