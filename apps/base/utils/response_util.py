import json
from datetime import datetime
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi import Response

from apps.base.enum.error_code import ErrorCode


class Result:
    def __init__(self, code=None, message=None, data=None):
        self.code = code or ErrorCode.SUCCESS.value[0]
        self.message = message or ErrorCode.SUCCESS.value[1]
        self.data = data

    def to_json(self):
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }


class ResponseUtil:

    @classmethod
    def success(cls, data: Any = None, error_code: ErrorCode = ErrorCode.SUCCESS):
        json_data = Result(*error_code.value, data=data).to_json()
        return cls._to_response(json_data)

    @classmethod
    def fail(cls, error_code: ErrorCode = ErrorCode.SERVICE_ERROR, data: Any = None):
        json_data = Result(*error_code.value, data=data).to_json()
        return cls._to_response(json_data)

    @classmethod
    def fail_cmd(cls, code: int = None, message: str = None, data: Any = None):
        code = code or ErrorCode.SERVICE_ERROR.value[0]
        message = message or ErrorCode.SERVICE_ERROR.value[1]
        json_data = Result(data=data, code=code, message=message).to_json()
        return cls._to_response(json_data)

    @classmethod
    def _to_response(cls, data: Any):
        data = cls._covert_data_type(data)
        data = jsonable_encoder(data)
        response = Response(json.dumps(data, ensure_ascii=False))
        response.headers["Content-Type"] = "application/json;charset=UTF-8"
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Connection"] = "close"
        return response

    @classmethod
    def _covert_data_type(cls, data: Any):
        if isinstance(data, dict):
            for k, v in data.items():
                data[k] = cls._covert_data_type(v)
        if isinstance(data, list):
            for i in range(len(data)):
                data[i] = cls._covert_data_type(data[i])
        if isinstance(data, int):
            data = str(data) if data > 2 ** 31 else data
        if isinstance(data, datetime):
            data = data.strftime("%Y-%m-%d %H:%M:%S")
        return data
