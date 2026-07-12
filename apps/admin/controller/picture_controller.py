from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.picture_service import AdminPictureService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.picture_vo import AdminPictureCreateVO, AdminPictureQueryVO, AdminPictureUpdateVO
from apps.admin.vo.status_vo import AdminCheckStatusVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/content", tags=["后台内容管理"])


@Controller(router)
class AdminPictureController:
    """后台图片控制器。"""

    admin_picture_service: AdminPictureService = Autowired()

    @router.get("/picture/list", summary="分页查询图片")
    @permission("content:picture:query")
    async def list_pictures(self, query_vo: AdminPictureQueryVO = Depends()) -> Response:
        """
        分页查询图片。

        :param query_vo: 图片查询参数
        :return: 图片分页数据
        """
        ret = await self.admin_picture_service.list_pictures(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/picture/{picture_id}", summary="查询图片详情")
    @permission("content:picture:query")
    async def get_picture(self, picture_id: int) -> Response:
        """
        查询图片详情。

        :param picture_id: 图片 ID
        :return: 图片详情
        """
        ret = await self.admin_picture_service.get_picture(picture_id)
        return ResponseUtil.success(ret)

    @router.post("/picture", summary="创建图片")
    @permission("content:picture:create")
    async def create_picture(self, picture_vo: AdminPictureCreateVO = Body()) -> Response:
        """
        创建图片。

        :param picture_vo: 图片创建参数
        :return: 图片详情
        """
        ret = await self.admin_picture_service.create_picture(picture_vo)
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
        ret = await self.admin_picture_service.update_picture(picture_id, picture_vo)
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
        ret = await self.admin_picture_service.update_picture_status(picture_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/picture/{picture_id}", summary="删除图片")
    @permission("content:picture:delete")
    async def delete_picture(self, picture_id: int) -> Response:
        """
        删除图片。

        :param picture_id: 图片 ID
        :return: 删除结果
        """
        await self.admin_picture_service.delete_picture(picture_id)
        return ResponseUtil.success()
