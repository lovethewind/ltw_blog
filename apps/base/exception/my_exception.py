from typing import Any

from apps.base.enum.error_code import ErrorCode


class MyException(Exception):

    def __init__(self, error_code: ErrorCode = ErrorCode.SERVICE_ERROR, data: Any = None):
        self.code = error_code.value[0]
        self.message = error_code.value[1]
        self.data = data

    @classmethod
    def param_err(cls, message: str = None, data: Any = None):
        exc = MyException()
        exc.code = ErrorCode.PARAM_ERROR.value[0]
        exc.message = message
        exc.data = data
        return exc

    @classmethod
    def not_found(cls, message: str = None, data: Any = None):
        exc = MyException()
        exc.code = ErrorCode.DATA_NOT_EXISTS.value[0]
        exc.message = message
        exc.data = data
        return exc

    @classmethod
    def error(cls, code: ErrorCode = ErrorCode.SERVICE_ERROR, message: str = None, data: Any = None):
        exc = MyException()
        exc.code = code.value[0]
        exc.message = message
        exc.data = data
        return exc

    def __str__(self):
        return f"{self.__class__.__name__}(code={self.code}, message={self.message}, data={self.data})"
