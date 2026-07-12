import math

from apps.admin.dao.article_dao import AdminArticleDao
from apps.admin.dto.article_dto import AdminArticleAuthorDTO, AdminArticleDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.article_vo import (
    AdminArticleCreateVO,
    AdminArticleQueryVO,
    AdminArticleStatusVO,
    AdminArticleUpdateVO,
)
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.article import Article
from apps.base.models.user import User


@Component()
class AdminArticleService(AdminBaseService):
    """后台文章服务。"""

    admin_article_dao: AdminArticleDao = Autowired()

    async def list_articles(self, query_vo: AdminArticleQueryVO) -> dict:
        """
        分页查询文章。

        :param query_vo: 文章查询参数
        :return: 文章分页数据
        """
        articles, total = await self.admin_article_dao.list_articles(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.category_id,
            query_vo.status,
            query_vo.user_id,
            query_vo.is_original,
        )
        author_map = await self.admin_article_dao.list_article_authors(list({article.user_id for article in articles}))
        records = [self._dump_article(article, author_map) for article in articles]
        return {
            "current": query_vo.current,
            "pages": math.ceil(total / query_vo.size) if query_vo.size else 0,
            "records": records,
            "size": query_vo.size,
            "total": total,
        }

    def _dump_article(self, article: Article, author_map: dict[int, User]) -> AdminArticleDTO:
        """
        转换文章响应数据，并附加作者摘要。

        :param article: 文章对象
        :param author_map: 用户 ID 到用户对象的映射
        :return: 文章响应数据
        """
        dto = AdminArticleDTO.model_validate(article)
        author = author_map.get(article.user_id)
        if author:
            dto.author = AdminArticleAuthorDTO.model_validate(author)
        return dto

    async def get_article(self, article_id: int) -> AdminArticleDTO:
        """
        查询文章详情。

        :param article_id: 文章 ID
        :return: 文章详情
        :raises MyException: 文章不存在时抛出
        """
        article = await self.admin_article_dao.get_article_by_id(article_id)
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        author_map = await self.admin_article_dao.list_article_authors([article.user_id])
        return self._dump_article(article, author_map)

    async def create_article(self, article_vo: AdminArticleCreateVO) -> AdminArticleDTO:
        """
        创建文章。

        :param article_vo: 文章创建参数
        :return: 文章详情
        """
        data = article_vo.model_dump(exclude_none=True)
        self._normalize_article_data(data)
        self._fill_thumbnail_url(data, "cover", "cover_thumb")
        article = await self.admin_article_dao.create_article(data)
        return AdminArticleDTO.model_validate(article)

    async def update_article(self, article_id: int, article_vo: AdminArticleUpdateVO) -> AdminArticleDTO:
        """
        更新文章。

        :param article_id: 文章 ID
        :param article_vo: 文章更新参数
        :return: 文章详情
        :raises MyException: 文章不存在时抛出
        """
        article = await self.admin_article_dao.get_article_by_id(article_id)
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = article_vo.model_dump(exclude_none=True)
        self._normalize_article_data(data)
        self._fill_thumbnail_url(data, "cover", "cover_thumb")
        article = await self.admin_article_dao.update_article(article, data)
        return AdminArticleDTO.model_validate(article)

    async def update_article_status(self, article_id: int, status_vo: AdminArticleStatusVO) -> AdminArticleDTO:
        """
        更新文章状态。

        :param article_id: 文章 ID
        :param status_vo: 状态更新参数
        :return: 文章详情
        :raises MyException: 文章不存在时抛出
        """
        article = await self.admin_article_dao.get_article_by_id(article_id)
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        article = await self.admin_article_dao.update_article(article, {"status": status_vo.status})
        return AdminArticleDTO.model_validate(article)

    async def delete_article(self, article_id: int) -> None:
        """
        删除文章。

        :param article_id: 文章 ID
        :return: None
        :raises MyException: 文章不存在时抛出
        """
        article = await self.admin_article_dao.get_article_by_id(article_id)
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_article_dao.delete_article(article_id)

    def _normalize_article_data(self, data: dict[str, object]) -> None:
        """
        规范化文章保存数据。

        :param data: 文章数据
        :return: None
        """
        for field in ("cover", "original_url"):
            if field in data and data[field] is None:
                data[field] = ""
        for field in ("tag_list", "attach_list"):
            if field in data and data[field] is None:
                data[field] = []
