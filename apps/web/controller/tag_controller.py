# @Time    : 2024/8/23 14:50
# @Author  : frank
# @File    : tag_controller.py
from fastapi import APIRouter
from fastapi import Depends

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.tag_service import TagService

router = APIRouter(prefix="/tag", tags=["标签模块"])


@Controller(router)
class TagController:
    tag_service: TagService = Autowired()

    @router.get("/common/findAll", summary="获取树形节点和所有")
    async def find_all(self):
        """
        获取树形节点和所有
        :return:
        """
        ret = await self.tag_service.find_all()
        return ResponseUtil.success(ret)
