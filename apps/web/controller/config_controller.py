# @Time    : 2024/8/23 14:29
# @Author  : frank
# @File    : config_controller.py
from email.utils import format_datetime

from fastapi import APIRouter, Request, Response
from starlette.responses import PlainTextResponse

from apps.base.core.depend_inject import Autowired, Controller
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

    @router.api_route(
        "/common/search-analysis/dictionary/{dictionary_type}", methods=["GET", "HEAD"], summary="获取 IK 远程词库"
    )
    async def get_search_analysis_dictionary(self, dictionary_type: str, request: Request) -> Response:
        """
        获取 IK 远程自定义词或停用词。

        :param dictionary_type: 词库类型。
        :param request: HTTP 请求。
        :return: 纯文本词库或 304 响应。
        """
        content, etag, updated_at = await self.configService.get_search_analysis_dictionary(dictionary_type)
        headers = {"ETag": etag, "Last-Modified": format_datetime(updated_at, usegmt=False)}
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers=headers)
        return PlainTextResponse(content, headers=headers)
