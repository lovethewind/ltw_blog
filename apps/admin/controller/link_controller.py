from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.link_service import AdminLinkService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.link_vo import AdminLinkCreateVO, AdminLinkQueryVO, AdminLinkUpdateVO
from apps.admin.vo.status_vo import AdminCheckStatusVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/link", tags=["后台友链管理"])


@Controller(router)
class AdminLinkController:
    """后台友链控制器。"""

    admin_link_service: AdminLinkService = Autowired()

    @router.get("/list", summary="分页查询友链")
    @permission("link:query")
    async def list_links(self, query_vo: AdminLinkQueryVO = Depends()) -> Response:
        """
        分页查询友链。

        :param query_vo: 友链查询参数
        :return: 友链分页数据
        """
        ret = await self.admin_link_service.list_links(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/{link_id}", summary="查询友链详情")
    @permission("link:query")
    async def get_link(self, link_id: int) -> Response:
        """
        查询友链详情。

        :param link_id: 友链 ID
        :return: 友链详情
        """
        ret = await self.admin_link_service.get_link(link_id)
        return ResponseUtil.success(ret)

    @router.post("/create", summary="创建友链")
    @permission("link:create")
    async def create_link(self, link_vo: AdminLinkCreateVO = Body()) -> Response:
        """
        创建友链。

        :param link_vo: 友链创建参数
        :return: 友链详情
        """
        ret = await self.admin_link_service.create_link(link_vo)
        return ResponseUtil.success(ret)

    @router.put("/{link_id}", summary="更新友链")
    @permission("link:update")
    async def update_link(self, link_id: int, link_vo: AdminLinkUpdateVO = Body()) -> Response:
        """
        更新友链。

        :param link_id: 友链 ID
        :param link_vo: 友链更新参数
        :return: 友链详情
        """
        ret = await self.admin_link_service.update_link(link_id, link_vo)
        return ResponseUtil.success(ret)

    @router.put("/{link_id}/status", summary="更新友链状态")
    @permission("link:status")
    async def update_link_status(self, link_id: int, status_vo: AdminCheckStatusVO = Body()) -> Response:
        """
        更新友链状态。

        :param link_id: 友链 ID
        :param status_vo: 状态更新参数
        :return: 友链详情
        """
        ret = await self.admin_link_service.update_link_status(link_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/{link_id}", summary="删除友链")
    @permission("link:delete")
    async def delete_link(self, link_id: int) -> Response:
        """
        删除友链。

        :param link_id: 友链 ID
        :return: 删除结果
        """
        await self.admin_link_service.delete_link(link_id)
        return ResponseUtil.success()
