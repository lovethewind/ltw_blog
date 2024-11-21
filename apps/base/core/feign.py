# @Time    : 2024/8/23 10:02
# @Author  : frank
# @File    : feign.py
import inspect
from typing import Type, Any

import aiohttp
from fastapi import UploadFile
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute
from pydantic import BaseModel
from typing_extensions import TypeVar

from .depend_inject import Component, ContainerUtil

T = TypeVar("T")


class FeignRouter:

    @classmethod
    def get(cls, path: str):
        return cls.request(method="get", path=path)

    @classmethod
    def post(cls, path: str):
        return cls.request(method="post", path=path)

    @classmethod
    def put(cls, path: str):
        return cls.request(method="put", path=path)

    @classmethod
    def delete(cls, path: str):
        return cls.request(method="delete", path=path)

    @classmethod
    def request(cls, method: str, path: str):
        def wrapper(func):
            old_signature = inspect.signature(func)
            new_signature = old_signature.replace(parameters=old_signature.parameters[1:])  # 去掉第一个参数
            func.__signature__ = new_signature
            route = APIRoute(path=path, endpoint=func, methods=[method], name=func.__name__)
            return_annotation = inspect.signature(func).return_annotation
            return Request(method=method, path=path, route=route, return_annotation=return_annotation)

        return wrapper


class RequestParam:

    def __init__(self):
        self.path = {}
        self.query = {}
        self.content = None  # text
        self.data = {}  # form-data
        self.files = {}  # form-data
        self.json = {}  # json
        self.errors = []

    def print_errors(self):
        err_str = "\n"
        for error in self.errors:
            err_str += f"{error}\n"
        return err_str


class Request:
    """
    升级了Fastapi版本，待优化
    """
    def __init__(self, method: str, path: str, route: APIRoute, return_annotation: Type[T]):
        self.url = None
        self.method = method
        self.path = path
        self.route = route
        self.return_annotation = return_annotation

    async def __call__(self, *args, headers: dict = None, **kwargs):
        param_vo = RequestParam()
        request_params = self._expand_params(args, kwargs)
        dependant = self.route.dependant
        self._get_path_params(param_vo, [dependant], request_params)
        self._get_query_params(param_vo, [dependant], request_params.copy())
        self._get_body_params(param_vo, [dependant], request_params)
        if param_vo.errors:
            raise Exception(param_vo.print_errors())
        url = f"{self.url}{self.path}".format(**param_vo.path)
        async with aiohttp.ClientSession() as session:
            ret = await session.request(self.method, url=url, headers=headers, **param_vo.json)
        if issubclass(self.return_annotation, BaseModel):
            return self.return_annotation(**await ret.json())
        return ret

    def _expand_params(self, args, kwargs):
        request_params = {}
        func_parameters = inspect.signature(self.route.endpoint).parameters
        func_parameters_list = list(func_parameters.items())
        for index, arg in enumerate(args):
            parameter_tuple = func_parameters_list[index]
            field = parameter_tuple[0]
            request_params[field] = arg
        request_params.update(kwargs)
        return request_params

    def _get_path_params(self, param_vo: RequestParam, dependencies: list[Dependant], request_params: dict):
        for dependant in dependencies:
            for param in dependant.path_params:
                val, err = param.validate(request_params.get(param.name))
                if err:
                    [item.update({"loc": ("path", param.name)}) for item in err]
                val = self._parse_val(val)
                param_vo.path[param.alias] = val
            self._get_path_params(param_vo, dependant.dependencies, request_params)

    def _get_query_params(self, param_vo: RequestParam, dependencies: list[Dependant], request_params: dict):
        for dependant in dependencies:
            if inspect.isclass(dependant.call) and issubclass(dependant.call, BaseModel):
                # query参数无法直接传一个对象，将其展开
                request_params.update(self._parse_val(request_params.get(dependant.name)))
            for param in dependant.query_params:
                val, err = param.validate(request_params.get(param.name))
                if err:
                    [item.update({"loc": ("query", param.name)}) for item in err]
                val = self._parse_val(val)
                param_vo.query[param.alias] = val
            self._get_query_params(param_vo, dependant.dependencies, request_params)

    def _get_body_params(self, param_vo: RequestParam, dependencies: list[Dependant], request_params: dict):
        for dependant in dependencies:
            for param in dependant.body_params:
                val, err = param.validate(request_params.get(param.name))
                if err:
                    [item.update({"loc": ("body", param.name)}) for item in err]
                    param_vo.errors.extend(err)
                val = self._parse_val(val)
                if param.field_info.media_type in ["application/x-www-form-urlencoded", "multipart/form-data"]:
                    if isinstance(val, UploadFile):
                        param_vo.files[param.alias] = (val.filename, val.file, val.content_type, val.headers)
                    else:
                        param_vo.data[param.alias] = val
                elif param.field_info.media_type == "application/json":
                    if param.field_info.embed:
                        param_vo.json[param.alias] = val
                    elif isinstance(val, (str, bytes)):
                        param_vo.content = val  # text
                        return
                    elif isinstance(val, dict):
                        param_vo.json.update(val)  # json对象
                    else:
                        param_vo.json = val  # json数组
                        return
            self._get_body_params(param_vo, dependant.dependencies, request_params)

    def _parse_val(self, val: Any):
        if isinstance(val, BaseModel):
            return val.model_dump()
        return val


class FeignClient:
    def __init__(self, server_name: str = None, url: str = None, component_name: str = None):
        self.server_name = server_name
        self.url = url
        self.component_name = component_name
        if not self.server_name and not self.url:
            raise Exception("server_name or url must be set")

    def __call__(self, cls: Type[T], *args, **kwargs):
        if not self.component_name:
            self.component_name = ContainerUtil.get_name_from_class(cls)
        for request_tuple in inspect.getmembers(cls, lambda x: isinstance(x, Request)):
            request: Request = request_tuple[1]
            request.url = self.url
        return Component(self.component_name)(cls)
