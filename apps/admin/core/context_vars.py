from contextvars import ContextVar

from starlette.requests import Request


class AdminContextVars:
    """
    后台管理上下文变量。
    """

    token_user_id: ContextVar[int | None] = ContextVar("admin_token_user_id", default=None)
    request: ContextVar[Request | None] = ContextVar("admin_request", default=None)
