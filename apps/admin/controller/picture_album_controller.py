from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.picture_album_service import AdminPictureAlbumService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.picture_album_vo import (
    AdminPictureAlbumCreateVO,
    AdminPictureAlbumQueryVO,
    AdminPictureAlbumUpdateVO,
)
from apps.admin.vo.status_vo import AdminCheckStatusVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/content", tags=["后台内容管理"])


@Controller(router)
class AdminPictureAlbumController:
    """后台相册控制器。"""

    admin_picture_album_service: AdminPictureAlbumService = Autowired()

    @router.get("/picture/album/list", summary="分页查询图册")
    @permission("content:pictureAlbum:query")
    async def list_picture_albums(self, query_vo: AdminPictureAlbumQueryVO = Depends()) -> Response:
        """
        分页查询图册。

        :param query_vo: 图册查询参数
        :return: 图册分页数据
        """
        ret = await self.admin_picture_album_service.list_picture_albums(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/picture/album/{album_id}", summary="查询图册详情")
    @permission("content:pictureAlbum:query")
    async def get_picture_album(self, album_id: int) -> Response:
        """
        查询图册详情。

        :param album_id: 图册 ID
        :return: 图册详情
        """
        ret = await self.admin_picture_album_service.get_picture_album(album_id)
        return ResponseUtil.success(ret)

    @router.post("/picture/album", summary="创建图册")
    @permission("content:pictureAlbum:create")
    async def create_picture_album(self, album_vo: AdminPictureAlbumCreateVO = Body()) -> Response:
        """
        创建图册。

        :param album_vo: 图册创建参数
        :return: 图册详情
        """
        ret = await self.admin_picture_album_service.create_picture_album(album_vo)
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
        ret = await self.admin_picture_album_service.update_picture_album(album_id, album_vo)
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
        ret = await self.admin_picture_album_service.update_picture_album_status(album_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/picture/album/{album_id}", summary="删除图册")
    @permission("content:pictureAlbum:delete")
    async def delete_picture_album(self, album_id: int) -> Response:
        """
        删除图册。

        :param album_id: 图册 ID
        :return: 删除结果
        """
        await self.admin_picture_album_service.delete_picture_album(album_id)
        return ResponseUtil.success()
