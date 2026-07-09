# @Time    : 2024/9/12 17:42
# @Author  : frank
# @File    : article_dao.py
import asyncio
from typing import Type

from sqlalchemy import func, select
from typing_extensions import TypeVar

from apps.base.core.depend_inject import Autowired, Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.article import ArticleStatusEnum
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

    async def get_article_detail_by_ids(
        self,
        article_ids: list[int] | None = None,
        articles: list[Article | ArticleListDTO] | None = None,
        clazz: Type[T] = ArticleListDTO,
    ) -> list[T]:
        """
        根据文章id/文章获取文章基本信息

        :param article_ids: 文章 ID 列表。
        :param articles: 已查询出的文章对象列表。
        :param clazz: 需要转换的 DTO 类型。
        :return: 文章详情 DTO 列表。
        """
        if not article_ids and not articles:
            return []
        if not articles:
            articles = await db.model_all(select(Article).where(Article.id.in_(article_ids)))
        ret = []
        for item in articles:
            record = clazz.model_validate(item, from_attributes=True)
            record.view_count, record.like_count, record.collect_count, record.comment_count = await asyncio.gather(
                self.redis_util.Article.get_article_view_count(record.id),
                self.redis_util.Article.get_article_like_count(record.id),
                self.redis_util.Article.get_article_collect_count(record.id),
                self.redis_util.Article.get_article_comment_count(record.id),
            )
            record.user = await manager.get_user_info(item.user_id, UserBaseInfoDTO)
            ret.append(record)
        return ret

    async def get_article(self, article_id: int) -> Article | None:
        """
        根据文章 ID 获取文章。

        :param article_id: 文章 ID。
        :return: 文章对象；不存在时返回 None。
        """
        return await db.model_first(select(Article).where(Article.id == article_id))

    async def get_user_article_count(self, user_id: int):
        stmt = (
            select(func.count(Article))
            .select_from(Article)
            .where(
                Article.user_id == user_id, Article.status == ArticleStatusEnum.PUBLISHED, Article.is_deleted == False
            )
        )
        return await db.scalar(stmt)
