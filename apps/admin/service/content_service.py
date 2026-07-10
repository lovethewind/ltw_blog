import math
from collections.abc import Sequence

from apps.admin.dao.content_dao import AdminContentDao
from apps.admin.dto.base_dto import BaseDTO
from apps.admin.dto.content_dto import (
    AdminArticleAuthorDTO,
    AdminArticleDTO,
    AdminCategoryDTO,
    AdminCommentDTO,
    AdminConfigDTO,
    AdminLinkDTO,
    AdminMessageDTO,
    AdminPictureAlbumDTO,
    AdminPictureDTO,
    AdminTagDTO,
    AdminWebsiteCategoryDTO,
    AdminWebsiteDTO,
)
from apps.admin.vo.content_vo import (
    AdminArticleCreateVO,
    AdminArticleQueryVO,
    AdminArticleStatusVO,
    AdminArticleUpdateVO,
    AdminCategoryCreateVO,
    AdminCategoryUpdateVO,
    AdminCheckStatusVO,
    AdminCommentQueryVO,
    AdminCommentStatusVO,
    AdminCommentUpdateVO,
    AdminConfigCreateVO,
    AdminConfigQueryVO,
    AdminConfigUpdateVO,
    AdminLinkCreateVO,
    AdminLinkQueryVO,
    AdminLinkUpdateVO,
    AdminMessageQueryVO,
    AdminMessageUpdateVO,
    AdminPictureAlbumCreateVO,
    AdminPictureAlbumQueryVO,
    AdminPictureAlbumUpdateVO,
    AdminPictureCreateVO,
    AdminPictureQueryVO,
    AdminPictureUpdateVO,
    AdminTagCreateVO,
    AdminTagUpdateVO,
    AdminWebsiteCategoryCreateVO,
    AdminWebsiteCategoryUpdateVO,
    AdminWebsiteCreateVO,
    AdminWebsiteQueryVO,
    AdminWebsiteUpdateVO,
)
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.article import Article
from apps.base.models.category import Tag
from apps.base.models.user import User


@Component()
class AdminContentService:
    """
    后台内容管理服务。
    """

    admin_content_dao: AdminContentDao = Autowired()

    async def list_articles(self, query_vo: AdminArticleQueryVO) -> dict:
        """
        分页查询文章。

        :param query_vo: 文章查询参数
        :return: 文章分页数据
        """
        articles, total = await self.admin_content_dao.list_articles(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.category_id,
            query_vo.status,
            query_vo.user_id,
            query_vo.is_original,
        )
        author_map = await self.admin_content_dao.list_article_authors(list({article.user_id for article in articles}))
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
        article = await self.admin_content_dao.get_article_by_id(article_id)
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        author_map = await self.admin_content_dao.list_article_authors([article.user_id])
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
        article = await self.admin_content_dao.create_article(data)
        return AdminArticleDTO.model_validate(article)

    async def update_article(self, article_id: int, article_vo: AdminArticleUpdateVO) -> AdminArticleDTO:
        """
        更新文章。

        :param article_id: 文章 ID
        :param article_vo: 文章更新参数
        :return: 文章详情
        :raises MyException: 文章不存在时抛出
        """
        article = await self.admin_content_dao.get_article_by_id(article_id)
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = article_vo.model_dump(exclude_none=True)
        self._normalize_article_data(data)
        self._fill_thumbnail_url(data, "cover", "cover_thumb")
        article = await self.admin_content_dao.update_article(article, data)
        return AdminArticleDTO.model_validate(article)

    async def update_article_status(self, article_id: int, status_vo: AdminArticleStatusVO) -> AdminArticleDTO:
        """
        更新文章状态。

        :param article_id: 文章 ID
        :param status_vo: 状态更新参数
        :return: 文章详情
        :raises MyException: 文章不存在时抛出
        """
        article = await self.admin_content_dao.get_article_by_id(article_id)
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        article = await self.admin_content_dao.update_article(article, {"status": status_vo.status})
        return AdminArticleDTO.model_validate(article)

    async def delete_article(self, article_id: int) -> None:
        """
        删除文章。

        :param article_id: 文章 ID
        :return: None
        :raises MyException: 文章不存在时抛出
        """
        article = await self.admin_content_dao.get_article_by_id(article_id)
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_content_dao.delete_article(article_id)

    async def list_comments(self, query_vo: AdminCommentQueryVO) -> dict:
        """
        分页查询评论。

        :param query_vo: 评论查询参数
        :return: 评论分页数据
        """
        comments, total = await self.admin_content_dao.list_comments(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.obj_id,
            query_vo.obj_type,
            query_vo.status,
            query_vo.user_id,
        )
        records = [AdminCommentDTO.model_validate(comment) for comment in comments]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_comment(self, comment_id: int) -> AdminCommentDTO:
        """
        查询评论详情。

        :param comment_id: 评论 ID
        :return: 评论详情
        :raises MyException: 评论不存在时抛出
        """
        comment = await self.admin_content_dao.get_comment_by_id(comment_id)
        if not comment:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminCommentDTO.model_validate(comment)

    async def update_comment(self, comment_id: int, comment_vo: AdminCommentUpdateVO) -> AdminCommentDTO:
        """
        更新评论。

        :param comment_id: 评论 ID
        :param comment_vo: 评论更新参数
        :return: 评论详情
        :raises MyException: 评论不存在时抛出
        """
        comment = await self.admin_content_dao.get_comment_by_id(comment_id)
        if not comment:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        comment = await self.admin_content_dao.update_comment(comment, comment_vo.model_dump(exclude_none=True))
        return AdminCommentDTO.model_validate(comment)

    async def update_comment_status(self, comment_id: int, status_vo: AdminCommentStatusVO) -> AdminCommentDTO:
        """
        更新评论状态。

        :param comment_id: 评论 ID
        :param status_vo: 状态更新参数
        :return: 评论详情
        :raises MyException: 评论不存在时抛出
        """
        comment = await self.admin_content_dao.get_comment_by_id(comment_id)
        if not comment:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        comment = await self.admin_content_dao.update_comment(comment, {"status": status_vo.status})
        return AdminCommentDTO.model_validate(comment)

    async def delete_comment(self, comment_id: int) -> None:
        """
        删除评论。

        :param comment_id: 评论 ID
        :return: None
        :raises MyException: 评论不存在时抛出
        """
        comment = await self.admin_content_dao.get_comment_by_id(comment_id)
        if not comment:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_content_dao.delete_comment(comment_id)

    async def list_messages(self, query_vo: AdminMessageQueryVO) -> dict:
        """
        分页查询留言。

        :param query_vo: 留言查询参数
        :return: 留言分页数据
        """
        messages, total = await self.admin_content_dao.list_messages(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.user_id,
            query_vo.parent_id,
        )
        records = [AdminMessageDTO.model_validate(message) for message in messages]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_message(self, message_id: int) -> AdminMessageDTO:
        """
        查询留言详情。

        :param message_id: 留言 ID
        :return: 留言详情
        :raises MyException: 留言不存在时抛出
        """
        message = await self.admin_content_dao.get_message_by_id(message_id)
        if not message:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminMessageDTO.model_validate(message)

    async def update_message(self, message_id: int, message_vo: AdminMessageUpdateVO) -> AdminMessageDTO:
        """
        更新留言。

        :param message_id: 留言 ID
        :param message_vo: 留言更新参数
        :return: 留言详情
        :raises MyException: 留言不存在时抛出
        """
        message = await self.admin_content_dao.get_message_by_id(message_id)
        if not message:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = message_vo.model_dump(exclude_none=True)
        self._normalize_message_data(data)
        message = await self.admin_content_dao.update_message(message, data)
        return AdminMessageDTO.model_validate(message)

    async def delete_message(self, message_id: int) -> None:
        """
        删除留言。

        :param message_id: 留言 ID
        :return: None
        :raises MyException: 留言不存在时抛出
        """
        message = await self.admin_content_dao.get_message_by_id(message_id)
        if not message:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_content_dao.delete_message(message_id)

    async def list_categories(self) -> list[AdminCategoryDTO]:
        """
        查询分类列表。

        :return: 分类列表
        """
        categories = await self.admin_content_dao.list_categories()
        return [AdminCategoryDTO.model_validate(category) for category in categories]

    async def create_category(self, category_vo: AdminCategoryCreateVO) -> AdminCategoryDTO:
        """
        创建分类。

        :param category_vo: 分类创建参数
        :return: 分类详情
        """
        data = category_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        category = await self.admin_content_dao.create_category(data)
        return AdminCategoryDTO.model_validate(category)

    async def update_category(self, category_id: int, category_vo: AdminCategoryUpdateVO) -> AdminCategoryDTO:
        """
        更新分类。

        :param category_id: 分类 ID
        :param category_vo: 分类更新参数
        :return: 分类详情
        :raises MyException: 分类不存在时抛出
        """
        category = await self.admin_content_dao.get_category_by_id(category_id)
        if not category:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = category_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        category = await self.admin_content_dao.update_category(category, data)
        return AdminCategoryDTO.model_validate(category)

    async def delete_category(self, category_id: int) -> None:
        """
        删除分类。

        :param category_id: 分类 ID
        :return: None
        :raises MyException: 分类不存在时抛出
        """
        category = await self.admin_content_dao.get_category_by_id(category_id)
        if not category:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_content_dao.delete_category(category_id)

    async def list_tag_tree(self, active_only: bool = False) -> list[AdminTagDTO]:
        """
        查询标签树。

        :param active_only: 是否只查询启用标签
        :return: 标签树
        """
        tags = await self.admin_content_dao.list_tags(active_only)
        return self._build_tag_tree(tags)

    async def create_tag(self, tag_vo: AdminTagCreateVO) -> AdminTagDTO:
        """
        创建标签。

        :param tag_vo: 标签创建参数
        :return: 标签详情
        """
        data = tag_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        tag = await self.admin_content_dao.create_tag(data)
        return AdminTagDTO.model_validate(tag)

    async def update_tag(self, tag_id: int, tag_vo: AdminTagUpdateVO) -> AdminTagDTO:
        """
        更新标签。

        :param tag_id: 标签 ID
        :param tag_vo: 标签更新参数
        :return: 标签详情
        :raises MyException: 标签不存在时抛出
        """
        tag = await self.admin_content_dao.get_tag_by_id(tag_id)
        if not tag:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = tag_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        if data.get("parent_id") == tag_id:
            raise MyException(ErrorCode.PARAM_ERROR)
        tag = await self.admin_content_dao.update_tag(tag, data)
        return AdminTagDTO.model_validate(tag)

    async def delete_tag(self, tag_id: int) -> None:
        """
        删除标签。

        :param tag_id: 标签 ID
        :return: None
        :raises MyException: 标签不存在或存在子级时抛出
        """
        tag = await self.admin_content_dao.get_tag_by_id(tag_id)
        if not tag:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        if await self.admin_content_dao.has_tag_children(tag_id):
            raise MyException(ErrorCode.MENU_HAS_SUB_ITEM)
        await self.admin_content_dao.delete_tag(tag_id)

    async def list_picture_albums(self, query_vo: AdminPictureAlbumQueryVO) -> dict:
        """
        分页查询图册。

        :param query_vo: 图册查询参数
        :return: 图册分页数据
        """
        albums, total = await self.admin_content_dao.list_picture_albums(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.status,
            query_vo.album_type,
            query_vo.user_id,
        )
        records = [AdminPictureAlbumDTO.model_validate(album) for album in albums]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_picture_album(self, album_id: int) -> AdminPictureAlbumDTO:
        """
        查询图册详情。

        :param album_id: 图册 ID
        :return: 图册详情
        :raises MyException: 图册不存在时抛出
        """
        album = await self.admin_content_dao.get_picture_album_by_id(album_id)
        if not album:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminPictureAlbumDTO.model_validate(album)

    async def create_picture_album(self, album_vo: AdminPictureAlbumCreateVO) -> AdminPictureAlbumDTO:
        """
        创建图册。

        :param album_vo: 图册创建参数
        :return: 图册详情
        """
        data = album_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        album = await self.admin_content_dao.create_picture_album(data)
        return AdminPictureAlbumDTO.model_validate(album)

    async def update_picture_album(self, album_id: int, album_vo: AdminPictureAlbumUpdateVO) -> AdminPictureAlbumDTO:
        """
        更新图册。

        :param album_id: 图册 ID
        :param album_vo: 图册更新参数
        :return: 图册详情
        :raises MyException: 图册不存在时抛出
        """
        album = await self.admin_content_dao.get_picture_album_by_id(album_id)
        if not album:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = album_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        album = await self.admin_content_dao.update_picture_album(album, data)
        return AdminPictureAlbumDTO.model_validate(album)

    async def update_picture_album_status(self, album_id: int, status_vo: AdminCheckStatusVO) -> AdminPictureAlbumDTO:
        """
        更新图册审核状态。

        :param album_id: 图册 ID
        :param status_vo: 审核状态参数
        :return: 图册详情
        :raises MyException: 图册不存在时抛出
        """
        album = await self.admin_content_dao.get_picture_album_by_id(album_id)
        if not album:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        album = await self.admin_content_dao.update_picture_album(album, {"status": status_vo.status})
        return AdminPictureAlbumDTO.model_validate(album)

    async def delete_picture_album(self, album_id: int) -> None:
        """
        删除图册。

        :param album_id: 图册 ID
        :return: None
        :raises MyException: 图册不存在时抛出
        """
        album = await self.admin_content_dao.get_picture_album_by_id(album_id)
        if not album:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_content_dao.delete_picture_album(album_id)

    async def list_pictures(self, query_vo: AdminPictureQueryVO) -> dict:
        """
        分页查询图片。

        :param query_vo: 图片查询参数
        :return: 图片分页数据
        """
        pictures, total = await self.admin_content_dao.list_pictures(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.album_id,
            query_vo.status,
            query_vo.user_id,
        )
        records = [AdminPictureDTO.model_validate(picture) for picture in pictures]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_picture(self, picture_id: int) -> AdminPictureDTO:
        """
        查询图片详情。

        :param picture_id: 图片 ID
        :return: 图片详情
        :raises MyException: 图片不存在时抛出
        """
        picture = await self.admin_content_dao.get_picture_by_id(picture_id)
        if not picture:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminPictureDTO.model_validate(picture)

    async def create_picture(self, picture_vo: AdminPictureCreateVO) -> AdminPictureDTO:
        """
        创建图片。

        :param picture_vo: 图片创建参数
        :return: 图片详情
        """
        data = picture_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        self._fill_thumbnail_url(data, "url", "thumb_url")
        picture = await self.admin_content_dao.create_picture(data)
        return AdminPictureDTO.model_validate(picture)

    async def update_picture(self, picture_id: int, picture_vo: AdminPictureUpdateVO) -> AdminPictureDTO:
        """
        更新图片。

        :param picture_id: 图片 ID
        :param picture_vo: 图片更新参数
        :return: 图片详情
        :raises MyException: 图片不存在时抛出
        """
        picture = await self.admin_content_dao.get_picture_by_id(picture_id)
        if not picture:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = picture_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        self._fill_thumbnail_url(data, "url", "thumb_url")
        picture = await self.admin_content_dao.update_picture(picture, data)
        return AdminPictureDTO.model_validate(picture)

    async def update_picture_status(self, picture_id: int, status_vo: AdminCheckStatusVO) -> AdminPictureDTO:
        """
        更新图片审核状态。

        :param picture_id: 图片 ID
        :param status_vo: 审核状态参数
        :return: 图片详情
        :raises MyException: 图片不存在时抛出
        """
        picture = await self.admin_content_dao.get_picture_by_id(picture_id)
        if not picture:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        picture = await self.admin_content_dao.update_picture(picture, {"status": status_vo.status})
        return AdminPictureDTO.model_validate(picture)

    async def delete_picture(self, picture_id: int) -> None:
        """
        删除图片。

        :param picture_id: 图片 ID
        :return: None
        :raises MyException: 图片不存在时抛出
        """
        picture = await self.admin_content_dao.get_picture_by_id(picture_id)
        if not picture:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_content_dao.delete_picture(picture_id)

    async def list_links(self, query_vo: AdminLinkQueryVO) -> dict:
        """
        分页查询友链。

        :param query_vo: 友链查询参数
        :return: 友链分页数据
        """
        links, total = await self.admin_content_dao.list_links(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.status,
        )
        records = [AdminLinkDTO.model_validate(link) for link in links]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_link(self, link_id: int) -> AdminLinkDTO:
        """
        查询友链详情。

        :param link_id: 友链 ID
        :return: 友链详情
        :raises MyException: 友链不存在时抛出
        """
        link = await self.admin_content_dao.get_link_by_id(link_id)
        if not link:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminLinkDTO.model_validate(link)

    async def create_link(self, link_vo: AdminLinkCreateVO) -> AdminLinkDTO:
        """
        创建友链。

        :param link_vo: 友链创建参数
        :return: 友链详情
        """
        data = link_vo.model_dump(exclude_none=True)
        self._normalize_link_data(data)
        link = await self.admin_content_dao.create_link(data)
        return AdminLinkDTO.model_validate(link)

    async def update_link(self, link_id: int, link_vo: AdminLinkUpdateVO) -> AdminLinkDTO:
        """
        更新友链。

        :param link_id: 友链 ID
        :param link_vo: 友链更新参数
        :return: 友链详情
        :raises MyException: 友链不存在时抛出
        """
        link = await self.admin_content_dao.get_link_by_id(link_id)
        if not link:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = link_vo.model_dump(exclude_none=True)
        self._normalize_link_data(data)
        link = await self.admin_content_dao.update_link(link, data)
        return AdminLinkDTO.model_validate(link)

    async def update_link_status(self, link_id: int, status_vo: AdminCheckStatusVO) -> AdminLinkDTO:
        """
        更新友链审核状态。

        :param link_id: 友链 ID
        :param status_vo: 审核状态参数
        :return: 友链详情
        :raises MyException: 友链不存在时抛出
        """
        link = await self.admin_content_dao.get_link_by_id(link_id)
        if not link:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        link = await self.admin_content_dao.update_link(link, {"status": status_vo.status})
        return AdminLinkDTO.model_validate(link)

    async def delete_link(self, link_id: int) -> None:
        """
        删除友链。

        :param link_id: 友链 ID
        :return: None
        :raises MyException: 友链不存在时抛出
        """
        link = await self.admin_content_dao.get_link_by_id(link_id)
        if not link:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_content_dao.delete_link(link_id)

    async def list_website_categories(self) -> list[AdminWebsiteCategoryDTO]:
        """
        查询网站导航分类列表。

        :return: 网站导航分类列表
        """
        categories = await self.admin_content_dao.list_website_categories()
        return [AdminWebsiteCategoryDTO.model_validate(category) for category in categories]

    async def create_website_category(self, category_vo: AdminWebsiteCategoryCreateVO) -> AdminWebsiteCategoryDTO:
        """
        创建网站导航分类。

        :param category_vo: 网站导航分类创建参数
        :return: 网站导航分类详情
        """
        category = await self.admin_content_dao.create_website_category(category_vo.model_dump(exclude_none=True))
        return AdminWebsiteCategoryDTO.model_validate(category)

    async def update_website_category(
        self, category_id: int, category_vo: AdminWebsiteCategoryUpdateVO
    ) -> AdminWebsiteCategoryDTO:
        """
        更新网站导航分类。

        :param category_id: 网站导航分类 ID
        :param category_vo: 网站导航分类更新参数
        :return: 网站导航分类详情
        :raises MyException: 网站导航分类不存在时抛出
        """
        category = await self.admin_content_dao.get_website_category_by_id(category_id)
        if not category:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        category = await self.admin_content_dao.update_website_category(
            category, category_vo.model_dump(exclude_none=True)
        )
        return AdminWebsiteCategoryDTO.model_validate(category)

    async def delete_website_category(self, category_id: int) -> None:
        """
        删除网站导航分类。

        :param category_id: 网站导航分类 ID
        :return: None
        :raises MyException: 网站导航分类不存在时抛出
        """
        category = await self.admin_content_dao.get_website_category_by_id(category_id)
        if not category:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_content_dao.delete_website_category(category_id)

    async def list_websites(self, query_vo: AdminWebsiteQueryVO) -> dict:
        """
        分页查询网站导航。

        :param query_vo: 网站导航查询参数
        :return: 网站导航分页数据
        """
        websites, total = await self.admin_content_dao.list_websites(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.category_id,
            query_vo.status,
            query_vo.user_id,
        )
        records = [AdminWebsiteDTO.model_validate(website) for website in websites]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_website(self, website_id: int) -> AdminWebsiteDTO:
        """
        查询网站导航详情。

        :param website_id: 网站导航 ID
        :return: 网站导航详情
        :raises MyException: 网站导航不存在时抛出
        """
        website = await self.admin_content_dao.get_website_by_id(website_id)
        if not website:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminWebsiteDTO.model_validate(website)

    async def create_website(self, website_vo: AdminWebsiteCreateVO) -> AdminWebsiteDTO:
        """
        创建网站导航。

        :param website_vo: 网站导航创建参数
        :return: 网站导航详情
        """
        data = website_vo.model_dump(exclude_none=True)
        self._normalize_website_data(data)
        website = await self.admin_content_dao.create_website(data)
        return AdminWebsiteDTO.model_validate(website)

    async def update_website(self, website_id: int, website_vo: AdminWebsiteUpdateVO) -> AdminWebsiteDTO:
        """
        更新网站导航。

        :param website_id: 网站导航 ID
        :param website_vo: 网站导航更新参数
        :return: 网站导航详情
        :raises MyException: 网站导航不存在时抛出
        """
        website = await self.admin_content_dao.get_website_by_id(website_id)
        if not website:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = website_vo.model_dump(exclude_none=True)
        self._normalize_website_data(data)
        website = await self.admin_content_dao.update_website(website, data)
        return AdminWebsiteDTO.model_validate(website)

    async def update_website_status(self, website_id: int, status_vo: AdminCheckStatusVO) -> AdminWebsiteDTO:
        """
        更新网站导航审核状态。

        :param website_id: 网站导航 ID
        :param status_vo: 审核状态参数
        :return: 网站导航详情
        :raises MyException: 网站导航不存在时抛出
        """
        website = await self.admin_content_dao.get_website_by_id(website_id)
        if not website:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        website = await self.admin_content_dao.update_website(website, {"status": status_vo.status})
        return AdminWebsiteDTO.model_validate(website)

    async def delete_website(self, website_id: int) -> None:
        """
        删除网站导航。

        :param website_id: 网站导航 ID
        :return: None
        :raises MyException: 网站导航不存在时抛出
        """
        website = await self.admin_content_dao.get_website_by_id(website_id)
        if not website:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_content_dao.delete_website(website_id)

    async def list_configs(self, query_vo: AdminConfigQueryVO) -> dict:
        """
        分页查询配置。

        :param query_vo: 配置查询参数
        :return: 配置分页数据
        """
        configs, total = await self.admin_content_dao.list_configs(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.is_active,
        )
        records = [AdminConfigDTO.model_validate(config) for config in configs]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_config(self, config_id: int) -> AdminConfigDTO:
        """
        查询配置详情。

        :param config_id: 配置 ID
        :return: 配置详情
        :raises MyException: 配置不存在时抛出
        """
        config = await self.admin_content_dao.get_config_by_id(config_id)
        if not config:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminConfigDTO.model_validate(config)

    async def create_config(self, config_vo: AdminConfigCreateVO) -> AdminConfigDTO:
        """
        创建配置。

        :param config_vo: 配置创建参数
        :return: 配置详情
        """
        data = config_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        config = await self.admin_content_dao.create_config(data)
        return AdminConfigDTO.model_validate(config)

    async def update_config(self, config_id: int, config_vo: AdminConfigUpdateVO) -> AdminConfigDTO:
        """
        更新配置。

        :param config_id: 配置 ID
        :param config_vo: 配置更新参数
        :return: 配置详情
        :raises MyException: 配置不存在时抛出
        """
        config = await self.admin_content_dao.get_config_by_id(config_id)
        if not config:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = config_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        config = await self.admin_content_dao.update_config(config, data)
        return AdminConfigDTO.model_validate(config)

    async def delete_config(self, config_id: int) -> None:
        """
        删除配置。

        :param config_id: 配置 ID
        :return: None
        :raises MyException: 配置不存在时抛出
        """
        config = await self.admin_content_dao.get_config_by_id(config_id)
        if not config:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_content_dao.delete_config(config_id)

    def _normalize_description(self, data: dict[str, object]) -> None:
        """
        规范化描述字段。

        :param data: 保存数据
        :return: None
        """
        if "description" in data and data["description"] is None:
            data["description"] = ""

    def _fill_thumbnail_url(self, data: dict[str, object], source_field: str, thumb_field: str) -> None:
        """
        在未传缩略图时使用原图地址兜底。

        :param data: 保存数据。
        :param source_field: 原图字段名。
        :param thumb_field: 缩略图字段名。
        :return: None
        """
        if source_field in data and not data.get(thumb_field):
            data[thumb_field] = data[source_field]

    def _normalize_link_data(self, data: dict[str, object]) -> None:
        """
        规范化友链保存数据。

        :param data: 友链数据
        :return: None
        """
        for field in ("cover", "description", "introduce"):
            if field in data and data[field] is None:
                data[field] = ""

    def _normalize_website_data(self, data: dict[str, object]) -> None:
        """
        规范化网站导航保存数据。

        :param data: 网站导航数据
        :return: None
        """
        for field in ("cover", "introduce"):
            if field in data and data[field] is None:
                data[field] = ""

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

    def _normalize_message_data(self, data: dict[str, object]) -> None:
        """
        规范化留言保存数据。

        :param data: 留言数据
        :return: None
        """
        for field in ("avatar", "nickname", "email", "address"):
            if field in data and data[field] is None:
                data[field] = ""

    def _page_result(self, current: int, size: int, total: int, records: Sequence[BaseDTO]) -> dict:
        """
        构建分页响应。

        :param current: 当前页码
        :param size: 每页条数
        :param total: 总数
        :param records: 数据列表
        :return: 分页响应
        """
        return {
            "current": current,
            "pages": math.ceil(total / size) if size else 0,
            "records": records,
            "size": size,
            "total": total,
        }

    def _build_tag_tree(self, tags: list[Tag]) -> list[AdminTagDTO]:
        """
        构建标签树。

        :param tags: 标签列表
        :return: 标签树
        """
        node_map = {tag.id: AdminTagDTO.model_validate(tag) for tag in tags}
        for node in node_map.values():
            node.children = []
        roots = []
        for tag in tags:
            node = node_map[tag.id]
            parent = node_map.get(tag.parent_id)
            if parent:
                parent.children.append(node)
            else:
                roots.append(node)
        return roots
