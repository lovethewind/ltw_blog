from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.source_service import AdminSourceService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.source_vo import AdminSourceQueryVO, AdminSourceUpdateVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/source", tags=["后台资源管理"])


@Controller(router)
class AdminSourceController:
    """后台资源控制器。"""

    admin_source_service: AdminSourceService = Autowired()

    @router.get("/list", summary="分页查询资源")
    @permission("source:query")
    async def list_sources(self, query_vo: AdminSourceQueryVO = Depends()) -> Response:
        """
        分页查询资源。

        :param query_vo: 资源查询参数
        :return: 资源分页数据
        """
        ret = await self.admin_source_service.list_sources(query_vo)
        return ResponseUtil.success(ret)

    @router.put("/{source_id}", summary="更新资源")
    @permission("source:update")
    async def update_source(self, source_id: int, source_vo: AdminSourceUpdateVO = Body()) -> Response:
        """
        更新资源。

        :param source_id: 资源 ID
        :param source_vo: 资源更新参数
        :return: 资源详情
        """
        ret = await self.admin_source_service.update_source(source_id, source_vo)
        return ResponseUtil.success(ret)

    @router.delete("/{source_id}", summary="删除资源")
    @permission("source:delete")
    async def delete_source(self, source_id: int) -> Response:
        """
        删除资源。

        :param source_id: 资源 ID
        :return: 删除结果
        """
        await self.admin_source_service.delete_source(source_id)
        return ResponseUtil.success()
