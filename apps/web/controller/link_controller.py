# @Time    : 2024/9/2 14:57
# @Author  : frank
# @File    : link_controller.py
from fastapi import APIRouter, Depends

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.link_service import LinkService
from apps.web.vo.link_vo import LinkVO

router = APIRouter(prefix="/link", tags=["友链模块"])


@Controller(router)
class LinkController:
    link_service: LinkService = Autowired()

    @router.get("/common/list", summary="获取友链列表")
    async def list_links(self):
        """
        获取友链列表
        :return:
        """
        ret = await self.link_service.list_links()
        return ResponseUtil.success(ret)

    @router.post("/common/add", summary="添加友链")
    async def add(self, link_vo: LinkVO):
        """
        添加网站导航
        :return:
        """
        await self.link_service.add(link_vo)
        return ResponseUtil.success()