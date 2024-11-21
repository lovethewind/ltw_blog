# @Time    : 2024/9/5 16:47
# @Author  : frank
# @File    : share_controller.py
from fastapi import APIRouter, Depends

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.share_service import ShareService
from apps.web.vo.batch_vo import BatchVO
from apps.web.vo.share_vo import ShareQueryVO, ShareAddVO, ShareUpdateVO

router = APIRouter(prefix="/share", tags=["分享模块"])


@Controller(router)
class ShareController:
    share_service: ShareService = Autowired()

    @router.get("/common/{current}/{size}", summary="查询分享列表")
    async def list_shares(self, current: int, size: int, share_query_vo: ShareQueryVO = Depends()):
        """
        查询分享列表
        :param current:
        :param size:
        :param share_query_vo:
        :return:
        """
        ret = await self.share_service.list_shares(current, size, share_query_vo)
        return ResponseUtil.success(ret)

    @router.get("/{current}/{size}", summary="查询分享列表")
    async def list_user_share(self, current: int, size: int, share_query_vo: ShareQueryVO = Depends()):
        """
        查询分享列表
        :param current:
        :param size:
        :param share_query_vo:
        :return:
        """
        ret = await self.share_service.list_shares(current, size, share_query_vo, is_user=True)
        return ResponseUtil.success(ret)

    @router.post("/add", summary="添加分享")
    async def add(self, share_add_vo: ShareAddVO):
        """
        添加分享
        :param share_add_vo:
        :return:
        """
        await self.share_service.add(share_add_vo)
        return ResponseUtil.success()

    @router.put("/update", summary="更新分享")
    async def update(self, share_update_vo: ShareUpdateVO):
        """
        更新分享
        :param share_update_vo:
        :return:
        """
        await self.share_service.update(share_update_vo)
        return ResponseUtil.success()

    @router.delete("/delete", summary="删除分享")
    async def delete(self, batch_vo: BatchVO):
        """
        删除分享
        :param batch_vo:
        :return:
        """
        await self.share_service.delete(batch_vo)
        return ResponseUtil.success()
