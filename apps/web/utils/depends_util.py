import functools

from fastapi import Header, Query
from starlette.requests import Request

from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.web.utils.token_util import TokenUtil


class DependsUtil:
    TOKEN_NAME = "web_token"

    @classmethod
    def get_user_id_from_token(cls, nullable: bool = False, token: str = Header(alias=TOKEN_NAME)):
        try:
            user_id = TokenUtil.get_user_id(token)
            return user_id
        except Exception as e:
            if nullable:
                return None
            raise e

    @classmethod
    def token_user_id(cls, nullable: bool = False):
        return functools.partial(cls.get_user_id_from_token, nullable=nullable)

    @classmethod
    def get_user_id_from_request(cls, request: Request, nullable: bool = True):
        try:
            token = request.headers.get(cls.TOKEN_NAME)
            if not token:
                raise MyException(ErrorCode.TOKEN_IS_EMPTY)
            user_id = TokenUtil.get_user_id(token)
            return user_id
        except Exception as e:
            if nullable:
                return None
            raise e

    @classmethod
    def ws_user_id(cls, token: str = Query()):
        user_id = TokenUtil.get_user_id(token)
        return user_id
