from fastapi import Body
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.category_service import AdminCategoryService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.category_vo import AdminCategoryCreateVO, AdminCategoryUpdateVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/content", tags=["后台内容管理"])


@Controller(router)
class AdminCategoryController:
    """后台分类控制器。"""

    admin_category_service: AdminCategoryService = Autowired()

    @router.get("/category/list", summary="查询分类列表")
    @permission("content:category:query")
    async def list_categories(self) -> Response:
        """
        查询分类列表。

        :return: 分类列表
        """
        ret = await self.admin_category_service.list_categories()
        return ResponseUtil.success(ret)

    @router.post("/category", summary="创建分类")
    @permission("content:category:create")
    async def create_category(self, category_vo: AdminCategoryCreateVO = Body()) -> Response:
        """
        创建分类。

        :param category_vo: 分类创建参数
        :return: 分类详情
        """
        ret = await self.admin_category_service.create_category(category_vo)
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
        ret = await self.admin_category_service.update_category(category_id, category_vo)
        return ResponseUtil.success(ret)

    @router.delete("/category/{category_id}", summary="删除分类")
    @permission("content:category:delete")
    async def delete_category(self, category_id: int) -> Response:
        """
        删除分类。

        :param category_id: 分类 ID
        :return: 删除结果
        """
        await self.admin_category_service.delete_category(category_id)
        return ResponseUtil.success()
