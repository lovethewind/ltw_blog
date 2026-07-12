import importlib
import json
import pkgutil
import time
from contextlib import asynccontextmanager
from json import JSONDecodeError
from typing import AsyncGenerator

from fastapi import APIRouter, FastAPI
from fastapi.concurrency import iterate_in_threadpool
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from apps.admin.config.logger_config import logger
from apps.admin.config.server_config import init_container_config
from apps.admin.core.context_vars import AdminContextVars
from apps.admin.utils.depends_util import AdminDependsUtil
from apps.base.core.depend_inject import GetValue
from apps.base.core.sqlalchemy.session import close_sqlalchemy_engine, init_sqlalchemy_engine
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.utils.response_util import ResponseUtil

init_container_config()


class AdminCreateApp:
    """
    后台管理 FastAPI 应用创建器。
    """

    def __init__(self, testing: bool = False, router_scan: list[str] | None = None, *args, **kwargs) -> None:
        """
        初始化后台管理应用创建器。

        :param testing: 是否使用测试配置
        :param router_scan: 路由扫描模块列表
        :return: None
        """
        super().__init__(*args, **kwargs)
        self.app = FastAPI(*args, lifespan=self._lifespan, **kwargs)
        self.testing = self.app.testing = testing
        self.router_scan = router_scan or []

    def init(self) -> FastAPI:
        """
        初始化后台管理 FastAPI 应用。

        :return: FastAPI 应用实例
        """
        self._register_router()
        self._add_exception_handler()
        self._add_middleware()
        return self.app

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:
        """
        管理后台管理 FastAPI 生命周期。

        :param app: FastAPI 应用实例
        :return: 生命周期异步生成器
        """
        init_sqlalchemy_engine()
        try:
            yield
        finally:
            await close_sqlalchemy_engine()

    def _register_router(self, router_name: str = "router", prefix: str = GetValue("app.context-path")) -> None:
        """
        注册后台管理路由。

        :param router_name: 路由变量名
        :param prefix: 全局接口前缀
        :return: None
        """
        router_scan = self.router_scan[:]
        admin_prefix = prefix or "/admin"
        for module in router_scan:
            if not module.endswith(".*"):
                m_router = getattr(importlib.import_module(module), router_name)
                self.app.include_router(m_router, prefix=admin_prefix)
                logger.info(f"注册后台路由[{m_router.prefix}]({module})成功")
            elif module.count(".*") != 1:
                logger.info(f"暂不支持 a.*.* 或 a.*.b的方式进行注册路由，跳过 {module}")
            else:
                m_module = importlib.import_module(module[:-2])
                for _, name, ispkg in pkgutil.iter_modules(m_module.__path__, prefix=module[:-1]):
                    if ispkg:
                        router_scan.append(f"{name}.*")
                    else:
                        m_router: APIRouter = getattr(importlib.import_module(name), router_name)
                        self.app.include_router(m_router, prefix=admin_prefix)
                        logger.info(f"注册后台路由[{m_router.prefix}]({module})成功")

    def _add_exception_handler(self) -> None:
        """
        添加后台管理异常处理。

        :return: None
        """

        @self.app.exception_handler(RequestValidationError)
        def validation_error_handler(request: Request, exc: RequestValidationError) -> Response:
            """
            替换默认的请求参数校验异常处理。

            :param request: 请求对象
            :param exc: 参数校验异常
            :return: 统一响应
            """
            logger.exception("admin_validation_error_handler", exc_info=exc)
            return ResponseUtil.fail(ErrorCode.PARAM_ERROR, exc.errors())

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
            """
            替换默认的 HTTP 异常处理。

            :param request: 请求对象
            :param exc: HTTP 异常
            :return: 统一响应
            """
            return ResponseUtil.fail_cmd(code=exc.status_code, message=exc.detail)

        @self.app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception) -> Response:
            """
            处理后台管理全局异常。

            :param request: 请求对象
            :param exc: 异常对象
            :return: 统一响应
            """
            if isinstance(exc, MyException):
                return ResponseUtil.fail_cmd(exc.code, exc.message, exc.data)
            logger.exception("admin_global_exception_handler", exc_info=exc)
            return ResponseUtil.fail(ErrorCode.SERVICE_ERROR)

    def _add_middleware(self) -> None:
        """
        添加后台管理中间件。

        :return: None
        """
        self.app.add_middleware(AdminHttpLogMiddleware)  # type: ignore
        self.app.add_middleware(AdminWhiteListMiddleware)  # type: ignore


class AdminHttpLogMiddleware(BaseHTTPMiddleware):
    """
    记录后台管理请求日志。
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        记录请求和响应摘要。

        :param request: 请求对象
        :param call_next: 下一个请求处理器
        :return: 响应对象
        """
        start_time = time.time()
        self.add_context_vars(request)
        request_body = await self.set_request_body(request)

        response = await call_next(request)

        if getattr(request.state, "log_request", None) is False:
            request_data = "-"
        else:
            try:
                request_data = json.dumps(json.loads(request_body), ensure_ascii=False)
            except JSONDecodeError, UnicodeDecodeError:
                request_data = await request.form()
                if not request_data:
                    request_data = "-"

        response_body = await self.set_response_body(response)
        if getattr(request.state, "log_response", None) is False:
            response_data = "-"
        else:
            try:
                response_data = json.dumps(json.loads(response_body), ensure_ascii=False)
            except JSONDecodeError, UnicodeDecodeError:
                response_data = response_body or "-"
        request_data = request_data[:500]
        response_data = response_data[:500]
        process_time = time.time() - start_time
        logger.info(
            f"[admin|{request.client.host}|{response.status_code}|{request.method}|{request.scope['path']}|"
            f"{request_data}|{response_data}|耗时:{process_time}]"
        )
        return response

    async def set_request_body(self, request: Request) -> bytes:
        """
        将请求数据变成可多次读取。

        :param request: 请求对象
        :return: 请求体字节
        """
        request_body = await request.body()
        return request_body

    async def set_response_body(self, response: Response) -> bytes:
        """
        将响应数据变成可多次读取。

        :param response: 响应对象
        :return: 响应体字节
        """
        response_body = b""
        if hasattr(response, "body_iterator"):
            async for chunk in response.body_iterator:
                response_body += chunk
            response.body_iterator = iterate_in_threadpool([response_body])
        else:
            response_body = response.body
        return response_body

    def add_context_vars(self, request: Request) -> None:
        """
        添加后台管理上下文变量。

        :param request: 请求对象
        :return: None
        """
        AdminContextVars.token_user_id.set(AdminDependsUtil.get_user_id_from_request(request))
        AdminContextVars.request.set(request)


class AdminWhiteListMiddleware(BaseHTTPMiddleware):
    """
    后台管理白名单中间件。
    """

    cache_whitelist: dict[str, bool] = {}
    base_whitelist = [
        "/openapi.json",
        "/admin/user/login",
        "/admin/common/health",
    ]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        校验后台管理请求是否需要登录。

        :param request: 请求对象
        :param call_next: 下一个请求处理器
        :return: 响应对象
        """
        config_whitelist = GetValue("app.admin.whitelist") or []
        whitelist: list[str] = config_whitelist + self.base_whitelist
        if not await self.is_in_whitelist(request, whitelist):
            try:
                AdminDependsUtil.get_user_id_from_request(request, nullable=False)
            except MyException as e:
                return ResponseUtil.fail_cmd(e.code, e.message)
        return await call_next(request)

    async def is_in_whitelist(self, request: Request, whitelist: list[str]) -> bool:
        """
        检查请求是否在白名单。

        :param request: 请求对象
        :param whitelist: 白名单路径列表
        :return: 是否在白名单
        """
        if not whitelist:
            return True
        request_path = request.url.path
        if request_path in self.cache_whitelist:
            return self.cache_whitelist.get(request_path, False)
        for white_path in whitelist:
            if request_path == white_path:
                self.cache_whitelist[request_path] = True
                return True
            if white_path.endswith("*") and request_path.startswith(white_path.rstrip("*")):
                self.cache_whitelist[request_path] = True
                return True
        self.cache_whitelist[request_path] = False
        return False


def create_app(testing: bool = False, router_scan: list[str] | None = None, *args, **kwargs) -> FastAPI:
    """
    创建后台管理 FastAPI 应用。

    :param testing: 是否使用测试配置
    :param router_scan: 路由扫描模块列表
    :return: FastAPI 应用实例
    """
    router_scan = router_scan or ["apps.admin.controller.*"]
    return AdminCreateApp(testing=testing, router_scan=router_scan, *args, **kwargs).init()
