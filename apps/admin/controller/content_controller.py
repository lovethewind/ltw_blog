from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.content_service import AdminContentService
from apps.admin.utils.depends_util import permission
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
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/content", tags=["后台内容管理"])


@Controller(router)
class AdminContentController:
    """
    后台内容管理控制器。
    """

    admin_content_service: AdminContentService = Autowired()

    @router.get("/article/list", summary="分页查询文章")
    @permission("content:article:query")
    async def list_articles(self, query_vo: AdminArticleQueryVO = Depends()) -> Response:
        """
        分页查询文章。

        :param query_vo: 文章查询参数
        :return: 文章分页数据
        """
        ret = await self.admin_content_service.list_articles(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/article/{article_id}", summary="查询文章详情")
    @permission("content:article:query")
    async def get_article(self, article_id: int) -> Response:
        """
        查询文章详情。

        :param article_id: 文章 ID
        :return: 文章详情
        """
        ret = await self.admin_content_service.get_article(article_id)
        return ResponseUtil.success(ret)

    @router.post("/article", summary="创建文章")
    @permission("content:article:create")
    async def create_article(self, article_vo: AdminArticleCreateVO = Body()) -> Response:
        """
        创建文章。

        :param article_vo: 文章创建参数
        :return: 文章详情
        """
        ret = await self.admin_content_service.create_article(article_vo)
        return ResponseUtil.success(ret)

    @router.put("/article/{article_id}", summary="更新文章")
    @permission("content:article:update")
    async def update_article(self, article_id: int, article_vo: AdminArticleUpdateVO = Body()) -> Response:
        """
        更新文章。

        :param article_id: 文章 ID
        :param article_vo: 文章更新参数
        :return: 文章详情
        """
        ret = await self.admin_content_service.update_article(article_id, article_vo)
        return ResponseUtil.success(ret)

    @router.put("/article/{article_id}/status", summary="更新文章状态")
    @permission("content:article:publish")
    async def update_article_status(self, article_id: int, status_vo: AdminArticleStatusVO = Body()) -> Response:
        """
        更新文章状态。

        :param article_id: 文章 ID
        :param status_vo: 状态更新参数
        :return: 文章详情
        """
        ret = await self.admin_content_service.update_article_status(article_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/article/{article_id}", summary="删除文章")
    @permission("content:article:delete")
    async def delete_article(self, article_id: int) -> Response:
        """
        删除文章。

        :param article_id: 文章 ID
        :return: 删除结果
        """
        await self.admin_content_service.delete_article(article_id)
        return ResponseUtil.success()

    @router.get("/comment/list", summary="分页查询评论")
    @permission("content:comment:query")
    async def list_comments(self, query_vo: AdminCommentQueryVO = Depends()) -> Response:
        """
        分页查询评论。

        :param query_vo: 评论查询参数
        :return: 评论分页数据
        """
        ret = await self.admin_content_service.list_comments(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/comment/{comment_id}", summary="查询评论详情")
    @permission("content:comment:query")
    async def get_comment(self, comment_id: int) -> Response:
        """
        查询评论详情。

        :param comment_id: 评论 ID
        :return: 评论详情
        """
        ret = await self.admin_content_service.get_comment(comment_id)
        return ResponseUtil.success(ret)

    @router.put("/comment/{comment_id}", summary="更新评论")
    @permission("content:comment:update")
    async def update_comment(self, comment_id: int, comment_vo: AdminCommentUpdateVO = Body()) -> Response:
        """
        更新评论。

        :param comment_id: 评论 ID
        :param comment_vo: 评论更新参数
        :return: 评论详情
        """
        ret = await self.admin_content_service.update_comment(comment_id, comment_vo)
        return ResponseUtil.success(ret)

    @router.put("/comment/{comment_id}/status", summary="更新评论状态")
    @permission("content:comment:status")
    async def update_comment_status(self, comment_id: int, status_vo: AdminCommentStatusVO = Body()) -> Response:
        """
        更新评论状态。

        :param comment_id: 评论 ID
        :param status_vo: 状态更新参数
        :return: 评论详情
        """
        ret = await self.admin_content_service.update_comment_status(comment_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/comment/{comment_id}", summary="删除评论")
    @permission("content:comment:delete")
    async def delete_comment(self, comment_id: int) -> Response:
        """
        删除评论。

        :param comment_id: 评论 ID
        :return: 删除结果
        """
        await self.admin_content_service.delete_comment(comment_id)
        return ResponseUtil.success()

    @router.get("/message/list", summary="分页查询留言")
    @permission("content:message:query")
    async def list_messages(self, query_vo: AdminMessageQueryVO = Depends()) -> Response:
        """
        分页查询留言。

        :param query_vo: 留言查询参数
        :return: 留言分页数据
        """
        ret = await self.admin_content_service.list_messages(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/message/{message_id}", summary="查询留言详情")
    @permission("content:message:query")
    async def get_message(self, message_id: int) -> Response:
        """
        查询留言详情。

        :param message_id: 留言 ID
        :return: 留言详情
        """
        ret = await self.admin_content_service.get_message(message_id)
        return ResponseUtil.success(ret)

    @router.put("/message/{message_id}", summary="更新留言")
    @permission("content:message:update")
    async def update_message(self, message_id: int, message_vo: AdminMessageUpdateVO = Body()) -> Response:
        """
        更新留言。

        :param message_id: 留言 ID
        :param message_vo: 留言更新参数
        :return: 留言详情
        """
        ret = await self.admin_content_service.update_message(message_id, message_vo)
        return ResponseUtil.success(ret)

    @router.delete("/message/{message_id}", summary="删除留言")
    @permission("content:message:delete")
    async def delete_message(self, message_id: int) -> Response:
        """
        删除留言。

        :param message_id: 留言 ID
        :return: 删除结果
        """
        await self.admin_content_service.delete_message(message_id)
        return ResponseUtil.success()

    @router.get("/category/list", summary="查询分类列表")
    @permission("content:category:query")
    async def list_categories(self) -> Response:
        """
        查询分类列表。

        :return: 分类列表
        """
        ret = await self.admin_content_service.list_categories()
        return ResponseUtil.success(ret)

    @router.post("/category", summary="创建分类")
    @permission("content:category:create")
    async def create_category(self, category_vo: AdminCategoryCreateVO = Body()) -> Response:
        """
        创建分类。

        :param category_vo: 分类创建参数
        :return: 分类详情
        """
        ret = await self.admin_content_service.create_category(category_vo)
        return ResponseUtil.success(ret)

    @router.put("/category/{category_id}", summary="更新分类")
    @permission("content:category:update")
    async def update_category(self, category_id: int, category_vo: AdminCategoryUpdateVO = Body()) -> Response:
        """
        更新分类。

        :param category_id: 分类 ID
        :param category_vo: 分类更新参数
        :return: 分类详情
        """
        ret = await self.admin_content_service.update_category(category_id, category_vo)
        return ResponseUtil.success(ret)

    @router.delete("/category/{category_id}", summary="删除分类")
    @permission("content:category:delete")
    async def delete_category(self, category_id: int) -> Response:
        """
        删除分类。

        :param category_id: 分类 ID
        :return: 删除结果
        """
        await self.admin_content_service.delete_category(category_id)
        return ResponseUtil.success()

    @router.get("/tag/tree", summary="查询标签树")
    @permission("content:tag:query")
    async def tag_tree(self, active_only: bool = False) -> Response:
        """
        查询标签树。

        :param active_only: 是否只查询启用标签
        :return: 标签树
        """
        ret = await self.admin_content_service.list_tag_tree(active_only)
        return ResponseUtil.success(ret)

    @router.post("/tag", summary="创建标签")
    @permission("content:tag:create")
    async def create_tag(self, tag_vo: AdminTagCreateVO = Body()) -> Response:
        """
        创建标签。

        :param tag_vo: 标签创建参数
        :return: 标签详情
        """
        ret = await self.admin_content_service.create_tag(tag_vo)
        return ResponseUtil.success(ret)

    @router.put("/tag/{tag_id}", summary="更新标签")
    @permission("content:tag:update")
    async def update_tag(self, tag_id: int, tag_vo: AdminTagUpdateVO = Body()) -> Response:
        """
        更新标签。

        :param tag_id: 标签 ID
        :param tag_vo: 标签更新参数
        :return: 标签详情
        """
        ret = await self.admin_content_service.update_tag(tag_id, tag_vo)
        return ResponseUtil.success(ret)

    @router.delete("/tag/{tag_id}", summary="删除标签")
    @permission("content:tag:delete")
    async def delete_tag(self, tag_id: int) -> Response:
        """
        删除标签。

        :param tag_id: 标签 ID
        :return: 删除结果
        """
        await self.admin_content_service.delete_tag(tag_id)
        return ResponseUtil.success()

    @router.get("/picture/album/list", summary="分页查询图册")
    @permission("content:pictureAlbum:query")
    async def list_picture_albums(self, query_vo: AdminPictureAlbumQueryVO = Depends()) -> Response:
        """
        分页查询图册。

        :param query_vo: 图册查询参数
        :return: 图册分页数据
        """
        ret = await self.admin_content_service.list_picture_albums(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/picture/album/{album_id}", summary="查询图册详情")
    @permission("content:pictureAlbum:query")
    async def get_picture_album(self, album_id: int) -> Response:
        """
        查询图册详情。

        :param album_id: 图册 ID
        :return: 图册详情
        """
        ret = await self.admin_content_service.get_picture_album(album_id)
        return ResponseUtil.success(ret)

    @router.post("/picture/album", summary="创建图册")
    @permission("content:pictureAlbum:create")
    async def create_picture_album(self, album_vo: AdminPictureAlbumCreateVO = Body()) -> Response:
        """
        创建图册。

        :param album_vo: 图册创建参数
        :return: 图册详情
        """
        ret = await self.admin_content_service.create_picture_album(album_vo)
        return ResponseUtil.success(ret)

    @router.put("/picture/album/{album_id}", summary="更新图册")
    @permission("content:pictureAlbum:update")
    async def update_picture_album(self, album_id: int, album_vo: AdminPictureAlbumUpdateVO = Body()) -> Response:
        """
        更新图册。

        :param album_id: 图册 ID
        :param album_vo: 图册更新参数
        :return: 图册详情
        """
        ret = await self.admin_content_service.update_picture_album(album_id, album_vo)
        return ResponseUtil.success(ret)

    @router.put("/picture/album/{album_id}/status", summary="更新图册状态")
    @permission("content:pictureAlbum:status")
    async def update_picture_album_status(self, album_id: int, status_vo: AdminCheckStatusVO = Body()) -> Response:
        """
        更新图册状态。

        :param album_id: 图册 ID
        :param status_vo: 状态更新参数
        :return: 图册详情
        """
        ret = await self.admin_content_service.update_picture_album_status(album_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/picture/album/{album_id}", summary="删除图册")
    @permission("content:pictureAlbum:delete")
    async def delete_picture_album(self, album_id: int) -> Response:
        """
        删除图册。

        :param album_id: 图册 ID
        :return: 删除结果
        """
        await self.admin_content_service.delete_picture_album(album_id)
        return ResponseUtil.success()

    @router.get("/picture/list", summary="分页查询图片")
    @permission("content:picture:query")
    async def list_pictures(self, query_vo: AdminPictureQueryVO = Depends()) -> Response:
        """
        分页查询图片。

        :param query_vo: 图片查询参数
        :return: 图片分页数据
        """
        ret = await self.admin_content_service.list_pictures(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/picture/{picture_id}", summary="查询图片详情")
    @permission("content:picture:query")
    async def get_picture(self, picture_id: int) -> Response:
        """
        查询图片详情。

        :param picture_id: 图片 ID
        :return: 图片详情
        """
        ret = await self.admin_content_service.get_picture(picture_id)
        return ResponseUtil.success(ret)

    @router.post("/picture", summary="创建图片")
    @permission("content:picture:create")
    async def create_picture(self, picture_vo: AdminPictureCreateVO = Body()) -> Response:
        """
        创建图片。

        :param picture_vo: 图片创建参数
        :return: 图片详情
        """
        ret = await self.admin_content_service.create_picture(picture_vo)
        return ResponseUtil.success(ret)

    @router.put("/picture/{picture_id}", summary="更新图片")
    @permission("content:picture:update")
    async def update_picture(self, picture_id: int, picture_vo: AdminPictureUpdateVO = Body()) -> Response:
        """
        更新图片。

        :param picture_id: 图片 ID
        :param picture_vo: 图片更新参数
        :return: 图片详情
        """
        ret = await self.admin_content_service.update_picture(picture_id, picture_vo)
        return ResponseUtil.success(ret)

    @router.put("/picture/{picture_id}/status", summary="更新图片状态")
    @permission("content:picture:status")
    async def update_picture_status(self, picture_id: int, status_vo: AdminCheckStatusVO = Body()) -> Response:
        """
        更新图片状态。

        :param picture_id: 图片 ID
        :param status_vo: 状态更新参数
        :return: 图片详情
        """
        ret = await self.admin_content_service.update_picture_status(picture_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/picture/{picture_id}", summary="删除图片")
    @permission("content:picture:delete")
    async def delete_picture(self, picture_id: int) -> Response:
        """
        删除图片。

        :param picture_id: 图片 ID
        :return: 删除结果
        """
        await self.admin_content_service.delete_picture(picture_id)
        return ResponseUtil.success()

    @router.get("/link/list", summary="分页查询友链")
    @permission("content:link:query")
    async def list_links(self, query_vo: AdminLinkQueryVO = Depends()) -> Response:
        """
        分页查询友链。

        :param query_vo: 友链查询参数
        :return: 友链分页数据
        """
        ret = await self.admin_content_service.list_links(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/link/{link_id}", summary="查询友链详情")
    @permission("content:link:query")
    async def get_link(self, link_id: int) -> Response:
        """
        查询友链详情。

        :param link_id: 友链 ID
        :return: 友链详情
        """
        ret = await self.admin_content_service.get_link(link_id)
        return ResponseUtil.success(ret)

    @router.post("/link", summary="创建友链")
    @permission("content:link:create")
    async def create_link(self, link_vo: AdminLinkCreateVO = Body()) -> Response:
        """
        创建友链。

        :param link_vo: 友链创建参数
        :return: 友链详情
        """
        ret = await self.admin_content_service.create_link(link_vo)
        return ResponseUtil.success(ret)

    @router.put("/link/{link_id}", summary="更新友链")
    @permission("content:link:update")
    async def update_link(self, link_id: int, link_vo: AdminLinkUpdateVO = Body()) -> Response:
        """
        更新友链。

        :param link_id: 友链 ID
        :param link_vo: 友链更新参数
        :return: 友链详情
        """
        ret = await self.admin_content_service.update_link(link_id, link_vo)
        return ResponseUtil.success(ret)

    @router.put("/link/{link_id}/status", summary="更新友链状态")
    @permission("content:link:status")
    async def update_link_status(self, link_id: int, status_vo: AdminCheckStatusVO = Body()) -> Response:
        """
        更新友链状态。

        :param link_id: 友链 ID
        :param status_vo: 状态更新参数
        :return: 友链详情
        """
        ret = await self.admin_content_service.update_link_status(link_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/link/{link_id}", summary="删除友链")
    @permission("content:link:delete")
    async def delete_link(self, link_id: int) -> Response:
        """
        删除友链。

        :param link_id: 友链 ID
        :return: 删除结果
        """
        await self.admin_content_service.delete_link(link_id)
        return ResponseUtil.success()

    @router.get("/website/category/list", summary="查询网站导航分类列表")
    @permission("content:websiteCategory:query")
    async def list_website_categories(self) -> Response:
        """
        查询网站导航分类列表。

        :return: 网站导航分类列表
        """
        ret = await self.admin_content_service.list_website_categories()
        return ResponseUtil.success(ret)

    @router.post("/website/category", summary="创建网站导航分类")
    @permission("content:websiteCategory:create")
    async def create_website_category(self, category_vo: AdminWebsiteCategoryCreateVO = Body()) -> Response:
        """
        创建网站导航分类。

        :param category_vo: 网站导航分类创建参数
        :return: 网站导航分类详情
        """
        ret = await self.admin_content_service.create_website_category(category_vo)
        return ResponseUtil.success(ret)

    @router.put("/website/category/{category_id}", summary="更新网站导航分类")
    @permission("content:websiteCategory:update")
    async def update_website_category(
        self,
        category_id: int,
        category_vo: AdminWebsiteCategoryUpdateVO = Body(),
    ) -> Response:
        """
        更新网站导航分类。

        :param category_id: 网站导航分类 ID
        :param category_vo: 网站导航分类更新参数
        :return: 网站导航分类详情
        """
        ret = await self.admin_content_service.update_website_category(category_id, category_vo)
        return ResponseUtil.success(ret)

    @router.delete("/website/category/{category_id}", summary="删除网站导航分类")
    @permission("content:websiteCategory:delete")
    async def delete_website_category(self, category_id: int) -> Response:
        """
        删除网站导航分类。

        :param category_id: 网站导航分类 ID
        :return: 删除结果
        """
        await self.admin_content_service.delete_website_category(category_id)
        return ResponseUtil.success()

    @router.get("/website/list", summary="分页查询网站导航")
    @permission("content:website:query")
    async def list_websites(self, query_vo: AdminWebsiteQueryVO = Depends()) -> Response:
        """
        分页查询网站导航。

        :param query_vo: 网站导航查询参数
        :return: 网站导航分页数据
        """
        ret = await self.admin_content_service.list_websites(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/website/{website_id}", summary="查询网站导航详情")
    @permission("content:website:query")
    async def get_website(self, website_id: int) -> Response:
        """
        查询网站导航详情。

        :param website_id: 网站导航 ID
        :return: 网站导航详情
        """
        ret = await self.admin_content_service.get_website(website_id)
        return ResponseUtil.success(ret)

    @router.post("/website", summary="创建网站导航")
    @permission("content:website:create")
    async def create_website(self, website_vo: AdminWebsiteCreateVO = Body()) -> Response:
        """
        创建网站导航。

        :param website_vo: 网站导航创建参数
        :return: 网站导航详情
        """
        ret = await self.admin_content_service.create_website(website_vo)
        return ResponseUtil.success(ret)

    @router.put("/website/{website_id}", summary="更新网站导航")
    @permission("content:website:update")
    async def update_website(self, website_id: int, website_vo: AdminWebsiteUpdateVO = Body()) -> Response:
        """
        更新网站导航。

        :param website_id: 网站导航 ID
        :param website_vo: 网站导航更新参数
        :return: 网站导航详情
        """
        ret = await self.admin_content_service.update_website(website_id, website_vo)
        return ResponseUtil.success(ret)

    @router.put("/website/{website_id}/status", summary="更新网站导航状态")
    @permission("content:website:status")
    async def update_website_status(self, website_id: int, status_vo: AdminCheckStatusVO = Body()) -> Response:
        """
        更新网站导航状态。

        :param website_id: 网站导航 ID
        :param status_vo: 状态更新参数
        :return: 网站导航详情
        """
        ret = await self.admin_content_service.update_website_status(website_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/website/{website_id}", summary="删除网站导航")
    @permission("content:website:delete")
    async def delete_website(self, website_id: int) -> Response:
        """
        删除网站导航。

        :param website_id: 网站导航 ID
        :return: 删除结果
        """
        await self.admin_content_service.delete_website(website_id)
        return ResponseUtil.success()

    @router.get("/config/list", summary="分页查询配置")
    @permission("content:config:query")
    async def list_configs(self, query_vo: AdminConfigQueryVO = Depends()) -> Response:
        """
        分页查询配置。

        :param query_vo: 配置查询参数
        :return: 配置分页数据
        """
        ret = await self.admin_content_service.list_configs(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/config/{config_id}", summary="查询配置详情")
    @permission("content:config:query")
    async def get_config(self, config_id: int) -> Response:
        """
        查询配置详情。

        :param config_id: 配置 ID
        :return: 配置详情
        """
        ret = await self.admin_content_service.get_config(config_id)
        return ResponseUtil.success(ret)

    @router.post("/config", summary="创建配置")
    @permission("content:config:create")
    async def create_config(self, config_vo: AdminConfigCreateVO = Body()) -> Response:
        """
        创建配置。

        :param config_vo: 配置创建参数
        :return: 配置详情
        """
        ret = await self.admin_content_service.create_config(config_vo)
        return ResponseUtil.success(ret)

    @router.put("/config/{config_id}", summary="更新配置")
    @permission("content:config:update")
    async def update_config(self, config_id: int, config_vo: AdminConfigUpdateVO = Body()) -> Response:
        """
        更新配置。

        :param config_id: 配置 ID
        :param config_vo: 配置更新参数
        :return: 配置详情
        """
        ret = await self.admin_content_service.update_config(config_id, config_vo)
        return ResponseUtil.success(ret)

    @router.delete("/config/{config_id}", summary="删除配置")
    @permission("content:config:delete")
    async def delete_config(self, config_id: int) -> Response:
        """
        删除配置。

        :param config_id: 配置 ID
        :return: 删除结果
        """
        await self.admin_content_service.delete_config(config_id)
        return ResponseUtil.success()
