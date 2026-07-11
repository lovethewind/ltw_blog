import asyncio
import copy
import inspect
import logging
import os
import threading
from pathlib import Path
from typing import Any, Awaitable, Optional, Type, get_type_hints

import yaml
from dependency_injector import containers, providers
from dependency_injector.errors import Error
from dependency_injector.providers import BaseSingleton
from dotenv import load_dotenv
from fastapi import APIRouter

from ..utils.path_util import PathUtil
from .cbv import cbv

logger = logging.getLogger(__name__)


class Container(containers.DynamicContainer):
    """
    依赖注入容器
    """

    config = providers.Configuration()  # 获取的配置
    refresh_scope = providers.Dict()  # 需要刷新的组件
    rv_dependent_dict = providers.Dict()  # 反向依赖查询使用


container = Container()


class ContainerUtil[T]:
    """
    依赖注入工具类
    """

    ENV_VAR = {
        "APP_ACTIVE": "app.active",
        "APP_CONTEXT_PATH": "app.context-path",
        "NACOS_USERNAME": "nacos.username",
        "NACOS_PASSWORD": "nacos.password",
    }
    ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
    NULL = object()
    _base_config: dict[str, Any] = {}
    _lock = threading.RLock()

    @classmethod
    def init(cls, resource_dir: str, server_config_class: Type[T], server_config_class_name: str = None):
        """
        初始化容器
        :param resource_dir: 资源目录位置
        :param server_config_class: 配置中心配置类(需实现get_config和add_watcher方法)
        :param server_config_class_name: 如果配置中心配置类组件名不为类名小驼峰，则需传入名字
        """
        server_config_class_name = server_config_class_name or cls.get_name_from_class(server_config_class)
        cls._init_container_config(resource_dir, server_config_class_name)

    @classmethod
    def _init_container_config(cls, resource_dir: str, server_config_class_name: str) -> None:
        """
        初始化配置，从配置文件中获取

        :param resource_dir: 资源目录位置
        :param server_config_class_name: 配置类 Bean 名称
        :return: None
        """
        bootstrap_file = PathUtil.join_path(resource_dir, "bootstrap.yaml", check_exist=True)
        container.config.from_yaml(bootstrap_file)
        cls._override_config_from_env()
        cls._base_config = copy.deepcopy(container.config())
        cls._init_config_from_server(server_config_class_name)

    @classmethod
    def _override_config_from_env(cls) -> None:
        """
        加载根目录 .env，并使用环境变量覆盖文件配置。

        系统环境变量优先级高于 .env 中的同名配置。

        :return: None。
        """
        load_dotenv(cls.ENV_FILE, override=False)
        for key, value in cls.ENV_VAR.items():
            env_value = os.environ.get(key, cls.NULL)
            if env_value is not cls.NULL:
                container.config.set(value, env_value)

    @classmethod
    def _init_config_from_server(cls, server_config_class_name: str):
        """
        从配置中心获取配置，配置类需实现get_config和add_watcher方法
        :param server_config_class_name: 配置类bean名称
        """
        server_config = cls.autowired(server_config_class_name)
        config = server_config.get_config()
        container.config.from_dict(config)
        logger.info(f"容器初始化配置，当前配置:[{server_config}]")
        server_config.add_watcher(cls._update_config_and_bean)

    @classmethod
    def _update_config_and_bean(cls, config: dict[str, object], *args: object, **kwargs: object) -> None:
        """
        更新配置并重置受影响的单例组件。

        :param config: 配置中心回调数据
        :param args: 配置中心附加位置参数
        :param kwargs: 配置中心附加关键字参数
        :return: None
        """
        try:
            content = config.get("content")
            if not isinstance(content, str) or not content.strip():
                raise ValueError("配置中心返回内容为空")
            server_config = yaml.safe_load(content)
            if not isinstance(server_config, dict):
                raise ValueError("配置中心返回内容必须为字典")
            new_config = providers.Configuration()
            new_config.from_dict(copy.deepcopy(cls._base_config))
            new_config.from_dict(server_config)
        except AttributeError, TypeError, ValueError, yaml.YAMLError:
            logger.exception("配置中心内容解析失败，保留当前配置")
            return

        with cls._lock:
            old_config = container.config
            update_component_set = set()
            for clazz, refresh_key_list in container.refresh_scope.kwargs.items():
                for refresh_key in refresh_key_list:
                    new_config_val = new_config.get(refresh_key)
                    old_config_val = old_config.get(refresh_key)
                    if new_config_val != old_config_val:
                        update_component_set.add(clazz)
                        break
            for clazz in tuple(update_component_set):
                cls._resolve_rv_dependent(clazz, update_component_set)

            container.config = new_config
            try:
                for clazz in update_component_set:
                    logger.info(f"组件[{clazz}]更新")
                    provider_bean = container.providers.get(cls.get_name_from_class(clazz))
                    if isinstance(provider_bean, BaseSingleton):
                        cls._close_singleton_instance(provider_bean)
                        provider_bean.reset()
            except Exception as e:
                container.config = old_config
                logger.exception(f"组件刷新失败，已恢复原配置 {e}")

    @classmethod
    def _close_singleton_instance(cls, provider_bean: BaseSingleton) -> None:
        """
        关闭待刷新的旧单例实例。

        :param provider_bean: 单例 Provider。
        :return: None。
        """
        instance = provider_bean()
        close_func = getattr(instance, "close", None)
        if not callable(close_func):
            return
        close_result = close_func()
        if inspect.isawaitable(close_result):
            cls._schedule_close(close_result)

    @classmethod
    def _schedule_close(cls, close_result: Awaitable[Any]) -> None:
        """
        执行或调度异步关闭任务。

        :param close_result: 异步关闭对象。
        :return: None。
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(close_result)
            return
        task = loop.create_task(close_result)
        task.add_done_callback(cls._log_close_task_exception)

    @staticmethod
    def _log_close_task_exception(task: asyncio.Task) -> None:
        """
        记录异步关闭任务异常。

        :param task: 异步关闭任务。
        :return: None。
        """
        try:
            task.result()
        except Exception as e:
            logger.exception(f"组件异步关闭失败: {e}")

    @classmethod
    def _resolve_rv_dependent(cls, clazz: Type[T], update_component_set: set[Type[T]]) -> None:
        """
        收集所有直接或间接依赖指定组件的组件。

        :param clazz: 被依赖的组件类
        :param update_component_set: 待刷新的组件集合，同时用于避免循环递归
        :return: None
        """
        rv_dependent_set = container.rv_dependent_dict.kwargs.get(clazz) or []
        for rv_dependent_cls in rv_dependent_set:
            if rv_dependent_cls in update_component_set:
                continue
            update_component_set.add(rv_dependent_cls)
            cls._resolve_rv_dependent(rv_dependent_cls, update_component_set)

    @classmethod
    def autowired(cls, name: str | Type[T]) -> T:
        """
        获取bean
        :param name: bean name or class
        :return: bean
        """
        with cls._lock:
            name = cls.get_name_from_class(name)
            try:
                bean = container.providers.get(name)()
                return bean
            except AttributeError as e:
                raise ValueError(f"get bean [{name}] error: {e}")

    @classmethod
    def get_bean_func(cls, name: str | Type[T]):
        """
        返回一个获取bean的方法，用于FastAPI调用注入参数
        """

        def wrapper():
            return cls.autowired(name)

        return wrapper

    @classmethod
    def get_config_value(cls, key: str, required: bool = False) -> Any:
        """
        获取配置值
        :param key: 配置key
        :param required: 是否必须
        :return: 配置值
        """
        with cls._lock:
            try:
                val = container.config.get(key, required=required)
            except Error:
                raise ValueError(f"配置[{key}]不存在，请检查配置是否正确")
            return val

    @classmethod
    def get_name_from_class(cls, cls_name: str | Type[T]):
        """
        获取类名
        :param cls_name: 类名
        :return: bean name
        """
        if not isinstance(cls_name, str):
            cls_name = cls_name.__name__[0].lower() + cls_name.__name__[1:]
        return cls_name


class Autowired[T]:
    """
    自动将定义的Bean添加至类__init__方法中，以实现自动注入，使用方法为
    在类中定义属性即可，示例如下:
    class A:
        redis_util: RedisUtil = Autowired()

    参数:
    name: 注册组件时的名称，可以为组件类本身，如果没有则使用类名(首字母小写)作为名称
    """

    def __init__(self, name: Optional[str | Type[T]] = None):
        self.name = name


class Value:
    """
    自动将定义的配置值添加至类__init__方法中，以实现自动注入值，使用方法为
    class A:
        server_name: str = Value("server.name")
    """

    def __init__(self, key: str):
        self.key = key


class Component[T]:
    """
    将组件注册成为容器中的Bean
    """

    def __init__(self, name: Optional[str] = None, singleton=True):
        self.name = name
        self.singleton = singleton

    def __call__(self, cls: Type[T], *args: object, **kwargs: object) -> Type[T]:
        """
        注册组件，并记录组件之间的反向依赖关系。

        :param cls: 待注册的组件类
        :param args: 装饰器附加位置参数
        :param kwargs: 装饰器附加关键字参数
        :return: 注册后的组件类
        """
        if not self.name:
            self.name = ContainerUtil.get_name_from_class(cls)
        if self.name in container.providers:
            raise ValueError(f"bean name [{self.name}] is already exists")
        provider_type = providers.Factory
        if self.singleton:
            provider_type = providers.ThreadSafeSingleton
        attr_type_dict = get_type_hints(cls)
        origin_init = cls.__init__

        for attr, attr_type in attr_type_dict.items():
            if not isinstance(getattr(cls, attr, None), Autowired):
                continue
            rv_dependent_set = set(container.rv_dependent_dict.kwargs.get(attr_type) or [])
            rv_dependent_set.add(cls)
            container.rv_dependent_dict.add_kwargs({attr_type: rv_dependent_set})

        def new_init(_self, *_args, **_kwargs):
            for attr, attr_type in attr_type_dict.items():
                v = getattr(cls, attr)
                if isinstance(v, Autowired):
                    setattr(_self, attr, GetBean(v.name or attr_type))
                elif isinstance(v, Value):
                    setattr(_self, attr, GetValue(v.key))
            origin_init(_self, *_args, **_kwargs)

        cls.__init__ = new_init
        container.providers.setdefault(self.name, provider_type(cls))
        return cls


class RefreshScope[T]:
    """
    标记需要刷新的注册组件
    """

    def __init__(self, refresh_key: str | list[str]):
        if not refresh_key:
            raise ValueError("组件刷新需要检查的key不能为空")
        if isinstance(refresh_key, str):
            refresh_key = [refresh_key]
        self.refresh_key = refresh_key

    def __call__(self, cls: Type[T], *args, **kwargs) -> Type[T]:
        container.refresh_scope.add_kwargs({cls: self.refresh_key})
        return cls


class Controller[T]:
    """
    将类标记为Controller，用于自动注册路由
    """

    def __init__(self, router: APIRouter, name: str | Type[T] = None, singleton=True):
        self.router = router
        self.name = name
        self.singleton = singleton

    def __call__(self, cls: Type[T], *args, **kwargs):
        if not self.name:
            self.name = ContainerUtil.get_name_from_class(cls)
        cls = Component(self.name, self.singleton)(cls)
        cls = cbv(self.router)(cls)
        return cls


GetBean = ContainerUtil.autowired
GetValue = ContainerUtil.get_config_value
BeanFunc = ContainerUtil.get_bean_func
