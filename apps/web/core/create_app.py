import importlib
import json
import pkgutil
import time
from json import JSONDecodeError

from fastapi import FastAPI, APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.concurrency import iterate_in_threadpool
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from tortoise.contrib.fastapi import register_tortoise

from apps.base.exception.my_exception import MyException
from apps.base.utils.response_util import ResponseUtil
from apps.base.enum.error_code import ErrorCode
from apps.base.core.depend_inject import ContainerUtil, GetValue, GetBean
from apps.web.config.logger_config import logger
from apps.web.config.nacos_config import NacosConfig
from apps.web.core.context_vars import ContextVars
from apps.web.core.kafka.util import KafkaUtil
from apps.web.utils.depends_util import DependsUtil
from apps.web.utils.path_util import PathUtil

# 先初始化容器配置
ContainerUtil.init(resource_dir=PathUtil.RESOURCE_PATH, server_config_class=NacosConfig)


class CreateApp:

    def __init__(self, testing: bool = False,
                 router_scan: list[str] = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = FastAPI(*args, **kwargs)
        self.testing = self.app.testing = testing
        self.router_scan = router_scan or []

    def init(self):
        self._db_init()
        self._register_router()
        self._add_exception_handler()
        self._add_middleware()
        self._kafka_start_consumer()
        return self.app

    def _kafka_start_consumer(self):
        kafka_util = GetBean(KafkaUtil)
        kafka_util.start_consumer()

    def _db_init(self, tortoise_config: dict = GetValue("app.db.tortoise"), testing_config: dict = GetValue("app.db.test-tortoise")):
        """
        初始化数据库连接
        """
        if self.testing:
            register_tortoise(self.app, testing_config)
            return
        register_tortoise(self.app, tortoise_config)

    def _register_router(self, router_name: str = "router", prefix: str = GetValue("app.context-path")):
        """
        注册路由
        :param router_name:
        :param prefix:
        :return:
        """
        router_scan = self.router_scan[:]
        for module in router_scan:
            if not module.endswith(".*"):
                m_router = getattr(importlib.import_module(module), router_name)
                self.app.include_router(m_router, prefix=prefix)
                logger.info(f"注册路由[{m_router.prefix}]({module})成功")
            elif module.count(".*") != 1:
                logger.info(f"暂不支持 a.*.* 或 a.*.b的方式进行注册路由，跳过 {module}")
            else:
                m_module = importlib.import_module(module[:-2])
                for _, name, ispkg in pkgutil.iter_modules(m_module.__path__, prefix=module[:-1]):
                    if ispkg:
                        router_scan.append(f"{name}.*")
                    else:
                        m_router: APIRouter = getattr(importlib.import_module(name), router_name)
                        self.app.include_router(m_router, prefix=prefix)
                        logger.info(f"注册路由[{m_router.prefix}]({module})成功")

    def _add_exception_handler(self):
        """
        添加异常处理
        :return:
        """

        @self.app.exception_handler(RequestValidationError)
        def validation_error_handler(request: Request, exc: RequestValidationError):
            """替换默认的RequestValidationError handler"""
            logger.exception("validation_error_handler", exc_info=exc)
            return ResponseUtil.fail(ErrorCode.PARAM_ERROR, exc.errors())

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            """替换默认的HTTPException handler"""
            return ResponseUtil.fail_cmd(code=exc.status_code, message=exc.detail)

        @self.app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            """全局Exception handler"""
            if isinstance(exc, MyException):
                return ResponseUtil.fail_cmd(exc.code, exc.message, exc.data)
            # logger.exception(f"global_exception_handler: {exc}")
            return ResponseUtil.fail_cmd(message=str(exc))

    def _add_middleware(self):
        """
        添加中间件
        :return:
        """
        self.app.add_middleware(HttpLogMiddleware)  # type: ignore
        self.app.add_middleware(WhiteListMiddleware)  # type: ignore


class HttpLogMiddleware(BaseHTTPMiddleware):
    """
    记录请求日志
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        self.add_context_vars(request)
        request_body = await self.set_request_body(request)

        response = await call_next(request)

        if getattr(request.state, "log_request", None) is False:
            request_data = "-"
        else:
            try:
                request_data = json.dumps(json.loads(request_body), ensure_ascii=False)
            except (JSONDecodeError, UnicodeDecodeError):
                request_data = await request.form()
                if not request_data:
                    request_data = "-"

        response_body = await self.set_response_body(response)
        if getattr(request.state, "log_response", None) is False:
            response_data = "-"
        else:
            try:
                response_data = json.dumps(json.loads(response_body), ensure_ascii=False)
            except (JSONDecodeError, UnicodeDecodeError):
                response_data = response_body or "-"
        request_data = request_data[:500]
        response_data = response_data[:500]
        process_time = time.time() - start_time
        logger.info(f"[{request.client.host}|{response.status_code}|{request.method}|{request.scope['path']}|"
                    f"{request_data}|{response_data}|耗时:{process_time}]")
        return response

    async def set_request_body(self, request: Request):
        """
        将请求数据变成可多次读取
        """
        # 只调用body()不调用stream()即可多次读取
        # 调用form()之前也需要调用body()，这样才会缓存body数据值_body属性，这里预先调用body()
        request_body = await request.body()
        return request_body

    async def set_response_body(self, response: Response):
        """将响应数据变成可多次读取"""
        response_body = b""
        if hasattr(response, "body_iterator"):
            async for chunk in response.body_iterator:
                response_body += chunk
            response.body_iterator = iterate_in_threadpool([response_body])
        else:
            response_body = response.body
        return response_body

    def add_context_vars(self, request: Request):
        """
        添加上下文变量
        :param request:
        :return:
        """
        ContextVars.token_user_id.set(DependsUtil.get_user_id_from_request(request))
        ContextVars.request.set(request)


class WhiteListMiddleware(BaseHTTPMiddleware):
    """
    白名单中间件
    """
    cache_whitelist = {}
    base_whitelist = [
        "/openapi.json"
    ]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        whitelist: list[str] = GetValue("app.whitelist") + self.base_whitelist
        if not await self.is_in_whitelist(request, whitelist):
            try:
                DependsUtil.get_user_id_from_request(request, nullable=False)
            except MyException as e:
                return ResponseUtil.fail_cmd(e.code, e.message)
        return await call_next(request)

    async def is_in_whitelist(self, request: Request, whitelist: list[str]):
        """
        检查请求是否在白名单
        :param request:
        :param whitelist:
        :return:
        """
        if not whitelist:
            return True
        request_path = request.url.path
        if request_path in self.cache_whitelist:
            return self.cache_whitelist.get(request_path)
        for white_path in whitelist:
            if request_path == white_path:
                self.cache_whitelist[request_path] = True
                return True
            if white_path.endswith("*") and request_path.startswith(white_path.rstrip("*")):
                self.cache_whitelist[request_path] = True
                return True
        self.cache_whitelist[request_path] = False
        return False


def create_app(testing=False, router_scan: list[str] = None, *args, **kwargs):
    router_scan = router_scan or ["apps.web.controller.*"]
    return CreateApp(testing=testing, router_scan=router_scan, *args, **kwargs).init()
