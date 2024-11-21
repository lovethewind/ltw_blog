# @Time    : 2024/8/23 14:29
# @Author  : frank
# @File    : config_controller.py
from fastapi import APIRouter

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.config_service import ConfigService

router = APIRouter(prefix="/config", tags=["配置模块"])


@Controller(router)
class ConfigController:
    configService: ConfigService = Autowired()

    @router.get("/common/detail/{key}", summary="根据key获取配置")
    async def get_config(self, key: str):
        """
        根据key获取配置
        :param key:
        :return:
        """
        ret = await self.configService.get_config(key)
        return ResponseUtil.success(ret)
