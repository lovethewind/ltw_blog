from fastapi import Body
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.website_category_service import AdminWebsiteCategoryService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.website_category_vo import AdminWebsiteCategoryCreateVO, AdminWebsiteCategoryUpdateVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/website/category", tags=["后台网站导航分类管理"])


@Controller(router)
class AdminWebsiteCategoryController:
    """后台网站导航分类控制器。"""

    admin_website_category_service: AdminWebsiteCategoryService = Autowired()

    @router.get("/list", summary="查询网站导航分类列表")
    @permission("websiteCategory:query")
    async def list_website_categories(self) -> Response:
        """
        查询网站导航分类列表。

        :return: 网站导航分类列表
        """
        ret = await self.admin_website_category_service.list_website_categories()
        return ResponseUtil.success(ret)

    @router.post("/create", summary="创建网站导航分类")
    @permission("websiteCategory:create")
    async def create_website_category(self, category_vo: AdminWebsiteCategoryCreateVO = Body()) -> Response:
        """
        创建网站导航分类。

        :param category_vo: 网站导航分类创建参数
        :return: 网站导航分类详情
        """
        ret = await self.admin_website_category_service.create_website_category(category_vo)
        return ResponseUtil.success(ret)

    @router.put("/{category_id}", summary="更新网站导航分类")
    @permission("websiteCategory:update")
    async def update_website_category(
        self, category_id: int, category_vo: AdminWebsiteCategoryUpdateVO = Body()
    ) -> Response:
        """
        更新网站导航分类。

        :param category_id: 网站导航分类 ID
        :param category_vo: 网站导航分类更新参数
        :return: 网站导航分类详情
        """
        ret = await self.admin_website_category_service.update_website_category(category_id, category_vo)
        return ResponseUtil.success(ret)

    @router.delete("/{category_id}", summary="删除网站导航分类")
    @permission("websiteCategory:delete")
    async def delete_website_category(self, category_id: int) -> Response:
        """
        删除网站导航分类。

        :param category_id: 网站导航分类 ID
        :return: 删除结果
        """
        await self.admin_website_category_service.delete_website_category(category_id)
        return ResponseUtil.success()
