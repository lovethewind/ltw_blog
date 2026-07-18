from fastapi import APIRouter, Depends, Response

from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.note_service import NoteService
from apps.web.vo.note_vo import NoteCreateVO, NotePinVO, NoteQueryVO, NoteUpdateVO

router = APIRouter(tags=["私人笔记"])


@Controller(router)
class NoteController:
    """私人笔记接口。"""

    note_service: NoteService = Autowired()

    @router.get("/note/list/{current}/{size}", summary="获取私人笔记列表")
    async def list_notes(self, current: int, size: int, note_query_vo: NoteQueryVO = Depends()) -> Response:
        """
        查询当前登录用户的私人笔记列表。

        :param current: 当前页码。
        :param size: 每页数量。
        :param note_query_vo: 笔记列表查询参数。
        :return: 统一成功响应。
        """
        ret = await self.note_service.list_notes(current, size, note_query_vo)
        return ResponseUtil.success(ret)

    @router.post("/note", summary="创建私人笔记")
    async def add(self, note_create_vo: NoteCreateVO) -> Response:
        """
        创建当前登录用户的私人笔记。

        :param note_create_vo: 笔记创建参数。
        :return: 包含新建笔记 ID 的统一成功响应。
        """
        ret = await self.note_service.add(note_create_vo)
        return ResponseUtil.success(ret)

    @router.get("/note/{note_id}", summary="获取私人笔记详情")
    async def detail(self, note_id: int) -> Response:
        """
        查询当前登录用户的私人笔记详情。

        :param note_id: 笔记 ID。
        :return: 包含笔记详情的统一成功响应。
        """
        ret = await self.note_service.detail(note_id)
        return ResponseUtil.success(ret)

    @router.put("/note/{note_id}", summary="更新私人笔记")
    async def update(self, note_id: int, note_update_vo: NoteUpdateVO) -> Response:
        """
        更新当前登录用户的私人笔记。

        :param note_id: 笔记 ID。
        :param note_update_vo: 笔记更新参数。
        :return: 统一成功响应。
        """
        await self.note_service.update(note_id, note_update_vo)
        return ResponseUtil.success()

    @router.get("/note/{note_id}/history/list/{current}/{size}", summary="获取私人笔记历史版本")
    async def list_history(self, note_id: int, current: int, size: int) -> Response:
        """
        分页查询当前登录用户指定笔记的历史版本。

        :param note_id: 笔记 ID。
        :param current: 当前页码。
        :param size: 每页数量。
        :return: 包含历史版本分页数据的统一成功响应。
        """
        ret = await self.note_service.list_history(note_id, current, size)
        return ResponseUtil.success(ret)

    @router.get("/note/{note_id}/history/{history_id}", summary="获取私人笔记历史版本详情")
    async def history_detail(self, note_id: int, history_id: int) -> Response:
        """
        查询当前登录用户指定笔记的历史版本详情。

        :param note_id: 笔记 ID。
        :param history_id: 历史版本 ID。
        :return: 包含历史版本详情的统一成功响应。
        """
        ret = await self.note_service.history_detail(note_id, history_id)
        return ResponseUtil.success(ret)

    @router.put("/note/{note_id}/history/{history_id}/restore", summary="恢复私人笔记历史版本")
    async def restore_history(self, note_id: int, history_id: int) -> Response:
        """
        恢复当前登录用户指定笔记的历史版本。

        :param note_id: 笔记 ID。
        :param history_id: 历史版本 ID。
        :return: 统一成功响应。
        """
        await self.note_service.restore_history(note_id, history_id)
        return ResponseUtil.success()

    @router.delete("/note/{note_id}/history/{history_id}", summary="删除私人笔记历史版本")
    async def delete_history(self, note_id: int, history_id: int) -> Response:
        """
        删除当前登录用户指定笔记的单个历史版本。

        :param note_id: 笔记 ID。
        :param history_id: 历史版本 ID。
        :return: 统一成功响应。
        """
        await self.note_service.delete_history(note_id, history_id)
        return ResponseUtil.success()

    @router.put("/note/{note_id}/pin", summary="设置私人笔记置顶状态")
    async def set_pinned(self, note_id: int, note_pin_vo: NotePinVO) -> Response:
        """
        设置当前登录用户私人笔记的置顶状态。

        :param note_id: 笔记 ID。
        :param note_pin_vo: 笔记置顶状态参数。
        :return: 统一成功响应。
        """
        await self.note_service.set_pinned(note_id, note_pin_vo)
        return ResponseUtil.success()

    @router.delete("/note/{note_id}", summary="移入私人笔记回收站")
    async def remove(self, note_id: int) -> Response:
        """
        将当前登录用户的私人笔记移入回收站。

        :param note_id: 笔记 ID。
        :return: 统一成功响应。
        """
        await self.note_service.remove(note_id)
        return ResponseUtil.success()

    @router.put("/note/{note_id}/restore", summary="恢复私人笔记")
    async def restore(self, note_id: int) -> Response:
        """
        恢复当前登录用户回收站中的私人笔记。

        :param note_id: 笔记 ID。
        :return: 统一成功响应。
        """
        await self.note_service.restore(note_id)
        return ResponseUtil.success()

    @router.delete("/note/{note_id}/permanent", summary="永久删除私人笔记")
    async def permanent_delete(self, note_id: int) -> Response:
        """
        永久删除当前登录用户回收站中的私人笔记。

        :param note_id: 笔记 ID。
        :return: 统一成功响应。
        """
        await self.note_service.permanent_delete(note_id)
        return ResponseUtil.success()
