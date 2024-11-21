# @Time    : 2024/9/1 22:49
# @Author  : frank
# @File    : website_controller.py
from fastapi import APIRouter
from fastapi.params import Depends

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.website_service import WebsiteService
from apps.web.vo.website_vo import WebsiteVO

router = APIRouter(prefix="/website", tags=["网站导航模块"])


@Controller(router)
class WebsiteController:
    website_service: WebsiteService = Autowired()

    @router.get("/common/list", summary="获取网站导航列表")
    async def list_websites(self):
        """
        获取网站导航列表
        :return:
        """
        ret = await self.website_service.list_websites()
        return ResponseUtil.success(ret)

    @router.post("/add", summary="添加网站导航")
    async def add(self, website_vo: WebsiteVO):
        """
        添加网站导航
        :return:
        """
        await self.website_service.add(website_vo)
        return ResponseUtil.success()
