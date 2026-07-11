import functools
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from fastapi import Header, Query
from sqlalchemy import func, select
from starlette.requests import Request

from apps.admin.core.context_vars import AdminContextVars
from apps.admin.utils.token_util import AdminTokenUtil
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.user import Menu, Role, RoleMenu, UserRole

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


class AdminDependsUtil:
    """
    后台管理依赖工具。
    """

    TOKEN_NAME = "admin_token"

    @classmethod
    def get_user_id_from_token(cls, nullable: bool = False, token: str = Header(alias=TOKEN_NAME)) -> int | None:
        """
        从后台 token 中解析用户 ID。

        :param nullable: 是否允许为空
        :param token: 后台 token
        :return: 用户 ID
        :raises MyException: token 缺失或无效时抛出
        """
        try:
            user_id = AdminTokenUtil.get_user_id(token)
            return user_id
        except Exception as e:
            if nullable:
                return None
            raise e

    @classmethod
    def token_user_id(cls, nullable: bool = False):
        """
        获取 FastAPI 依赖形式的后台用户 ID 解析函数。

        :param nullable: 是否允许为空
        :return: 后台用户 ID 解析函数
        """
        return functools.partial(cls.get_user_id_from_token, nullable=nullable)

    @classmethod
    def get_user_id_from_request(cls, request: Request, nullable: bool = True) -> int | None:
        """
        从请求头解析后台用户 ID。

        :param request: 请求对象
        :param nullable: 是否允许为空
        :return: 用户 ID
        :raises MyException: token 缺失或无效时抛出
        """
        try:
            token = request.headers.get(cls.TOKEN_NAME)
            if not token:
                raise MyException(ErrorCode.TOKEN_IS_EMPTY)
            user_id = AdminTokenUtil.get_user_id(token)
            return user_id
        except Exception as e:
            if nullable:
                return None
            raise e

    @classmethod
    def ws_user_id(cls, token: str = Query()) -> int | None:
        """
        从 WebSocket token 参数解析后台用户 ID。

        :param token: 后台 token
        :return: 用户 ID
        """
        user_id = AdminTokenUtil.get_user_id(token)
        return user_id

    @classmethod
    async def check_permission(cls, code: str) -> None:
        """
        校验当前后台用户是否拥有指定权限码。

        :param code: 权限标识
        :return: None
        :raises MyException: 用户未登录或没有权限时抛出
        """
        user_id = AdminContextVars.token_user_id.get()
        if user_id is None:
            request = AdminContextVars.request.get()
            if request is not None:
                user_id = cls.get_user_id_from_request(request, nullable=False)
        if user_id is None:
            raise MyException(ErrorCode.TOKEN_IS_EMPTY)
        if not await cls.has_permission(user_id, code):
            raise MyException(ErrorCode.NO_PERMISSION)

    @classmethod
    async def has_permission(cls, user_id: int, code: str) -> bool:
        """
        判断后台用户是否拥有指定权限码。

        :param user_id: 用户 ID。
        :param code: 权限标识。
        :return: 拥有权限返回 True，否则返回 False。
        """
        stmt = (
            select(func.count(Menu.id))
            .select_from(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .join(RoleMenu, RoleMenu.role_id == Role.id)
            .join(Menu, Menu.id == RoleMenu.menu_id)
            .where(
                UserRole.user_id == user_id,
                Role.is_active.is_(True),
                Menu.code == code,
                Menu.is_active.is_(True),
            )
        )
        return bool(await db.scalar(stmt))


def permission(code: str) -> Callable[[F], F]:
    """
    创建后台接口权限校验装饰器。

    :param code: 权限标识
    :return: 权限校验装饰器
    """

    def decorator(func: F) -> F:
        """
        包装后台接口处理方法。

        :param func: 接口处理方法
        :return: 已添加权限校验的接口处理方法
        """

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            执行权限校验并调用原始接口方法。

            :param args: 位置参数
            :param kwargs: 关键字参数
            :return: 原始接口返回值
            """
            await AdminDependsUtil.check_permission(code)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
