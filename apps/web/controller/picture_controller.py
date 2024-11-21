# @Time    : 2024/9/3 14:05
# @Author  : frank
# @File    : picture_controller.py
from fastapi import APIRouter
from fastapi.params import Depends

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.picture_service import PictureService
from apps.web.vo.batch_vo import BatchVO
from apps.web.vo.picture_vo import PictureQueryVO, PictureAddVO, PictureAlbumAddVO, PictureUpdateVO, \
    PictureAlbumUpdateVO

router = APIRouter(prefix="/picture", tags=["图片模块"])


@Controller(router)
class PictureController:
    picture_service: PictureService = Autowired()

    @router.get("/common/album/{current}/{size}", summary="获取图库列表")
    async def list_album(self, current: int, size: int):
        """
        获取图库列表
        :param current:
        :param size:
        :return:
        """
        ret = await self.picture_service.list_album(current, size)
        return ResponseUtil.success(ret)

    @router.get("/album/{current}/{size}", summary="获取某人图库列表")
    async def list_user_album(self, current: int, size: int):
        """
        获取图库列表
        :param current:
        :param size:
        :return:
        """
        ret = await self.picture_service.list_album(current, size, is_user=True)
        return ResponseUtil.success(ret)

    @router.post("/album/add", summary="添加图库分类")
    async def add_album(self, picture_album_add_vo: PictureAlbumAddVO):
        """
        添加图库分类
        :param picture_album_add_vo:
        :return:
        """
        ret = await self.picture_service.add_album(picture_album_add_vo)
        return ResponseUtil.success(ret)

    @router.put("/album/update", summary="更新图库分类")
    async def update_album(self, picture_album_update_vo: PictureAlbumUpdateVO):
        """
        更新图库分类
        :param picture_album_update_vo:
        :return:
        """
        await self.picture_service.update_album(picture_album_update_vo)
        return ResponseUtil.success()

    @router.delete("/album/delete/{album_id}", summary="删除图库分类")
    async def delete_album(self, album_id: int):
        """
        删除图库分类
        :param album_id:
        :return:
        """
        await self.picture_service.delete_album(album_id)
        return ResponseUtil.success()

    @router.get("/common/picture/{current}/{size}", summary="查询图片列表")
    async def list_picture(self, current: int, size: int, picture_query_vo: PictureQueryVO = Depends()):
        """
        查询图片列表
        :param current:
        :param size:
        :param picture_query_vo:
        :return:
        """
        ret = await self.picture_service.list_picture(current, size, picture_query_vo)
        return ResponseUtil.success(ret)

    @router.get("/picture/{current}/{size}", summary="查询图片列表")
    async def list_user_picture(self, current: int, size: int, picture_query_vo: PictureQueryVO = Depends()):
        """
        查询图片列表
        :param current:
        :param size:
        :param picture_query_vo:
        :return:
        """
        ret = await self.picture_service.list_picture(current, size, picture_query_vo, is_user=True)
        return ResponseUtil.success(ret)

    @router.post("/add", summary="添加图片")
    async def add_picture(self, picture_add_vo: PictureAddVO):
        """
        添加图片
        :param picture_add_vo:
        :return:
        """
        ret = await self.picture_service.add_picture(picture_add_vo)
        return ResponseUtil.success(ret)

    @router.put("/update", summary="更新图片信息")
    async def update_picture(self, picture_update_vo: PictureUpdateVO):
        """
        更新图片信息
        :param picture_update_vo:
        :return:
        """
        await self.picture_service.update_picture(picture_update_vo)
        return ResponseUtil.success()

    @router.delete("/delete", summary="(批量)删除图片")
    async def delete_picture(self, batch_vo: BatchVO):
        """
        删除图片
        :param batch_vo:
        :return:
        """
        await self.picture_service.delete_picture(batch_vo)
        return ResponseUtil.success()
