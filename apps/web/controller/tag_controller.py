# @Time    : 2024/8/23 14:50
# @Author  : frank
# @File    : tag_controller.py
from fastapi import APIRouter, Response

from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.tag_service import TagService
from apps.web.vo.tag_vo import TagCreateVO

router = APIRouter(prefix="/tag", tags=["标签模块"])


@Controller(router)
class TagController:
    tag_service: TagService = Autowired()

    @router.post("/add", summary="创建或复用自定义标签")
    async def create_or_get(self, tag_vo: TagCreateVO) -> Response:
        """
        创建未分组的自定义标签，同名标签已存在时直接复用。

        :param tag_vo: 自定义标签创建参数。
        :return: 创建或复用的标签详情。
        """
        ret = await self.tag_service.create_or_get(tag_vo)
        return ResponseUtil.success(ret)

    @router.get("/common/findAll", summary="获取树形节点和所有")
    async def find_all(self):
        """
        获取树形节点和所有
        :return:
        """
        ret = await self.tag_service.find_all()
        return ResponseUtil.success(ret)
