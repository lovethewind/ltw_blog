from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.article_service import AdminArticleService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.article_vo import (
    AdminArticleCreateVO,
    AdminArticleQueryVO,
    AdminArticleStatusVO,
    AdminArticleUpdateVO,
)
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/content", tags=["后台内容管理"])


@Controller(router)
class AdminArticleController:
    """后台文章控制器。"""

    admin_article_service: AdminArticleService = Autowired()

    @router.get("/article/list", summary="分页查询文章")
    @permission("content:article:query")
    async def list_articles(self, query_vo: AdminArticleQueryVO = Depends()) -> Response:
        """
        分页查询文章。

        :param query_vo: 文章查询参数
        :return: 文章分页数据
        """
        ret = await self.admin_article_service.list_articles(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/article/{article_id}", summary="查询文章详情")
    @permission("content:article:query")
    async def get_article(self, article_id: int) -> Response:
        """
        查询文章详情。

        :param article_id: 文章 ID
        :return: 文章详情
        """
        ret = await self.admin_article_service.get_article(article_id)
        return ResponseUtil.success(ret)

    @router.post("/article", summary="创建文章")
    @permission("content:article:create")
    async def create_article(self, article_vo: AdminArticleCreateVO = Body()) -> Response:
        """
        创建文章。

        :param article_vo: 文章创建参数
        :return: 文章详情
        """
        ret = await self.admin_article_service.create_article(article_vo)
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
        ret = await self.admin_article_service.update_article(article_id, article_vo)
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
        ret = await self.admin_article_service.update_article_status(article_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/article/{article_id}", summary="删除文章")
    @permission("content:article:delete")
    async def delete_article(self, article_id: int) -> Response:
        """
        删除文章。

        :param article_id: 文章 ID
        :return: 删除结果
        """
        await self.admin_article_service.delete_article(article_id)
        return ResponseUtil.success()
