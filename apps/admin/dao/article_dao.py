from typing import Any

from sqlalchemy import or_, select

from apps.admin.dao.base_dao import _create, _delete, _paginate, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.article import Article
from apps.base.models.user import User


@Component()
class AdminArticleDao:
    """后台文章数据访问对象。"""

    async def list_articles(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        category_id: int | None = None,
        status: int | None = None,
        user_id: int | None = None,
        is_original: bool | None = None,
    ) -> tuple[list[Article], int]:
        """
        分页查询文章。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 标题关键词。
        :param category_id: 分类 ID。
        :param status: 文章状态。
        :param user_id: 用户 ID。
        :param is_original: 是否原创。
        :return: 文章列表和总数。
        """
        stmt = select(Article)
        if keyword:
            stmt = stmt.where(or_(Article.title.ilike(f"%{keyword}%"), Article.content.ilike(f"%{keyword}%")))
        if category_id:
            stmt = stmt.where(Article.category_id == category_id)
        if status is not None:
            stmt = stmt.where(Article.status == status)
        if user_id:
            stmt = stmt.where(Article.user_id == user_id)
        if is_original is not None:
            stmt = stmt.where(Article.is_original == is_original)
        return await _paginate(stmt, current, size, Article.id.desc())

    async def list_article_authors(self, user_ids: list[int]) -> dict[int, User]:
        """
        批量查询文章作者。

        :param user_ids: 用户 ID 列表。
        :return: 用户 ID 到用户对象的映射。
        """
        if not user_ids:
            return {}
        users = await db.model_all(select(User).where(User.id.in_(user_ids)))
        return {user.id: user for user in users}

    async def get_article_by_id(self, article_id: int) -> Article | None:
        """
        根据 ID 查询文章。

        :param article_id: 文章 ID。
        :return: 文章对象。
        """
        return await db.model_first(select(Article).where(Article.id == article_id))

    async def create_article(self, data: dict[str, Any]) -> Article:
        """
        创建文章。

        :param data: 文章数据。
        :return: 文章对象。
        """
        return await _create(Article, data)

    async def update_article(self, article: Article, data: dict[str, Any]) -> Article:
        """
        更新文章。

        :param article: 文章对象。
        :param data: 更新数据。
        :return: 文章对象。
        """
        return await _update(article, data)

    async def delete_article(self, article_id: int) -> None:
        """
        删除文章。

        :param article_id: 文章 ID。
        :return: None。
        """
        await _delete(Article, article_id)
