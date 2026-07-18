from fastapi import APIRouter, Query, Response

from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.note_folder_service import NoteFolderService
from apps.web.vo.note_folder_vo import NoteFolderSortVO, NoteFolderVO

router = APIRouter(tags=["私人笔记文件夹"])


@Controller(router)
class NoteFolderController:
    """私人笔记文件夹接口。"""

    note_folder_service: NoteFolderService = Autowired()

    @router.get("/note-folder/list", summary="获取私人笔记文件夹列表")
    async def list(self, is_deleted: bool = Query(default=False, alias="isDeleted")) -> Response:
        """
        查询当前登录用户的私人笔记文件夹列表。

        :return: 包含文件夹列表的统一成功响应。
        """
        ret = await self.note_folder_service.list(is_deleted=is_deleted)
        return ResponseUtil.success(ret)

    @router.post("/note-folder", summary="创建私人笔记文件夹")
    async def add(self, note_folder_vo: NoteFolderVO) -> Response:
        """
        创建当前登录用户的私人笔记文件夹。

        :param note_folder_vo: 文件夹新增参数。
        :return: 包含新建文件夹的统一成功响应。
        """
        ret = await self.note_folder_service.add(note_folder_vo)
        return ResponseUtil.success(ret)

    @router.put("/note-folder/sort", summary="更新私人笔记文件夹排序")
    async def update_sort(self, note_folder_sort_vo: NoteFolderSortVO) -> Response:
        """
        更新当前登录用户的私人笔记文件夹排序。

        :param note_folder_sort_vo: 文件夹排序参数。
        :return: 统一成功响应。
        """
        await self.note_folder_service.update_sort(note_folder_sort_vo)
        return ResponseUtil.success()

    @router.put("/note-folder/{folder_id}", summary="重命名私人笔记文件夹")
    async def rename(self, folder_id: int, note_folder_vo: NoteFolderVO) -> Response:
        """
        重命名当前登录用户的私人笔记文件夹。

        :param folder_id: 文件夹 ID。
        :param note_folder_vo: 文件夹名称参数。
        :return: 统一成功响应。
        """
        await self.note_folder_service.rename(folder_id, note_folder_vo)
        return ResponseUtil.success()

    @router.delete("/note-folder/{folder_id}", summary="删除私人笔记文件夹")
    async def delete(self, folder_id: int) -> Response:
        """
        删除当前登录用户的私人笔记文件夹。

        :param folder_id: 文件夹 ID。
        :return: 统一成功响应。
        """
        await self.note_folder_service.delete(folder_id)
        return ResponseUtil.success()

    @router.put("/note-folder/{folder_id}/restore", summary="恢复私人笔记文件夹")
    async def restore(self, folder_id: int) -> Response:
        """
        恢复当前用户回收站中的文件夹子树。

        :param folder_id: 根文件夹 ID。
        :return: 统一成功响应。
        """
        await self.note_folder_service.restore(folder_id)
        return ResponseUtil.success()

    @router.delete("/note-folder/{folder_id}/permanent", summary="永久删除私人笔记文件夹")
    async def permanent_delete(self, folder_id: int) -> Response:
        """
        永久删除当前用户回收站中的文件夹子树。

        :param folder_id: 根文件夹 ID。
        :return: 统一成功响应。
        """
        await self.note_folder_service.permanent_delete(folder_id)
        return ResponseUtil.success()
