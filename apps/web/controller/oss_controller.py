# @Time    : 2024/9/1 19:27
# @Author  : frank
# @File    : oss_controller.py
from fastapi import APIRouter
from fastapi import Depends

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.oss_service import OssService
from apps.web.vo.oss_vo import GetSignatureVO

router = APIRouter(prefix="/oss", tags=["oss模块"])


@Controller(router)
class OssController:

    oss_service: OssService = Autowired()

    @router.post("/getSignatureUrl", summary="获取签名url")
    async def get_signature_url(self, get_signature_vo: GetSignatureVO):
        """
        获取签名
        :param get_signature_vo:
        :return:
        """
        ret = await self.oss_service.get_signature_url(get_signature_vo)
        return ResponseUtil.success(ret)
