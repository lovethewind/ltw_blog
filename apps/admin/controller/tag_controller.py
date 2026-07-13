from fastapi import Body
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.tag_service import AdminTagService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.tag_vo import AdminTagCreateVO, AdminTagUpdateVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/tag", tags=["后台标签管理"])


@Controller(router)
class AdminTagController:
    """后台标签控制器。"""

    admin_tag_service: AdminTagService = Autowired()

    @router.get("/tree", summary="查询标签树")
    @permission("tag:query")
    async def tag_tree(self, active_only: bool = False) -> Response:
        """
        查询标签树。

        :param active_only: 是否只查询启用标签
        :return: 标签树
        """
        ret = await self.admin_tag_service.list_tag_tree(active_only)
        return ResponseUtil.success(ret)

    @router.post("/create", summary="创建标签")
    @permission("tag:create")
    async def create_tag(self, tag_vo: AdminTagCreateVO = Body()) -> Response:
        """
        创建标签。

        :param tag_vo: 标签创建参数
        :return: 标签详情
        """
        ret = await self.admin_tag_service.create_tag(tag_vo)
        return ResponseUtil.success(ret)

    @router.put("/{tag_id}", summary="更新标签")
    @permission("tag:update")
    async def update_tag(self, tag_id: int, tag_vo: AdminTagUpdateVO = Body()) -> Response:
        """
        更新标签。

        :param tag_id: 标签 ID
        :param tag_vo: 标签更新参数
        :return: 标签详情
        """
        ret = await self.admin_tag_service.update_tag(tag_id, tag_vo)
        return ResponseUtil.success(ret)

    @router.delete("/{tag_id}", summary="删除标签")
    @permission("tag:delete")
    async def delete_tag(self, tag_id: int) -> Response:
        """
        删除标签。

        :param tag_id: 标签 ID
        :return: 删除结果
        """
        await self.admin_tag_service.delete_tag(tag_id)
        return ResponseUtil.success()
