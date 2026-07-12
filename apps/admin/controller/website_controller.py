from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.website_service import AdminWebsiteService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.status_vo import AdminCheckStatusVO
from apps.admin.vo.website_vo import AdminWebsiteCreateVO, AdminWebsiteQueryVO, AdminWebsiteUpdateVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/content", tags=["后台内容管理"])


@Controller(router)
class AdminWebsiteController:
    """后台网站导航控制器。"""

    admin_website_service: AdminWebsiteService = Autowired()

    @router.get("/website/list", summary="分页查询网站导航")
    @permission("content:website:query")
    async def list_websites(self, query_vo: AdminWebsiteQueryVO = Depends()) -> Response:
        """
        分页查询网站导航。

        :param query_vo: 网站导航查询参数
        :return: 网站导航分页数据
        """
        ret = await self.admin_website_service.list_websites(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/website/{website_id}", summary="查询网站导航详情")
    @permission("content:website:query")
    async def get_website(self, website_id: int) -> Response:
        """
        查询网站导航详情。

        :param website_id: 网站导航 ID
        :return: 网站导航详情
        """
        ret = await self.admin_website_service.get_website(website_id)
        return ResponseUtil.success(ret)

    @router.post("/website", summary="创建网站导航")
    @permission("content:website:create")
    async def create_website(self, website_vo: AdminWebsiteCreateVO = Body()) -> Response:
        """
        创建网站导航。

        :param website_vo: 网站导航创建参数
        :return: 网站导航详情
        """
        ret = await self.admin_website_service.create_website(website_vo)
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
        ret = await self.admin_website_service.update_website(website_id, website_vo)
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
        ret = await self.admin_website_service.update_website_status(website_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/website/{website_id}", summary="删除网站导航")
    @permission("content:website:delete")
    async def delete_website(self, website_id: int) -> Response:
        """
        删除网站导航。

        :param website_id: 网站导航 ID
        :return: 删除结果
        """
        await self.admin_website_service.delete_website(website_id)
        return ResponseUtil.success()
