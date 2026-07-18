from fastapi import APIRouter, Response

from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.note_tag_service import NoteTagService
from apps.web.vo.note_tag_vo import NoteTagVO

router = APIRouter(tags=["私人笔记标签"])


@Controller(router)
class NoteTagController:
    """私人笔记标签接口。"""

    note_tag_service: NoteTagService = Autowired()

    @router.get("/note-tag/list", summary="获取私人笔记标签列表")
    async def list(self) -> Response:
        """
        查询当前登录用户的私人笔记标签列表。

        :return: 包含标签列表的统一成功响应。
        """
        ret = await self.note_tag_service.list()
        return ResponseUtil.success(ret)

    @router.post("/note-tag", summary="创建私人笔记标签")
    async def add(self, note_tag_vo: NoteTagVO) -> Response:
        """
        创建当前登录用户的私人笔记标签。

        :param note_tag_vo: 标签新增参数。
        :return: 包含新建标签的统一成功响应。
        """
        ret = await self.note_tag_service.add(note_tag_vo)
        return ResponseUtil.success(ret)

    @router.put("/note-tag/{tag_id}", summary="重命名私人笔记标签")
    async def rename(self, tag_id: int, note_tag_vo: NoteTagVO) -> Response:
        """
        重命名当前登录用户的私人笔记标签。

        :param tag_id: 标签 ID。
        :param note_tag_vo: 标签名称参数。
        :return: 统一成功响应。
        """
        await self.note_tag_service.rename(tag_id, note_tag_vo)
        return ResponseUtil.success()

    @router.delete("/note-tag/{tag_id}", summary="删除私人笔记标签")
    async def delete(self, tag_id: int) -> Response:
        """
        删除当前登录用户的私人笔记标签。

        :param tag_id: 标签 ID。
        :return: 统一成功响应。
        """
        await self.note_tag_service.delete(tag_id)
        return ResponseUtil.success()
