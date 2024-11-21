# @Time    : 2024/8/11 19:12
# @Author  : frank
# @File    : context_vars.py
from contextvars import ContextVar

from starlette.requests import Request


class ContextVars:
    request = ContextVar[Request]("request")
    token_user_id = ContextVar[int]("token_user_id")
