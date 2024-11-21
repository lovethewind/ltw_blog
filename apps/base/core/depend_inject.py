import logging
import os
import threading
from typing import Type, get_type_hints

import yaml
from fastapi import APIRouter
from dependency_injector import containers, providers
from dependency_injector.errors import Error
from dependency_injector.providers import BaseSingleton

from .cbv import cbv
from ..utils.path_util import PathUtil

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
        "APP_CONTEXT_PATH": "app.context-path"
    }
    NULL = object()
    _condition = threading.Condition()
    _lock = threading.Lock()

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
    def _init_container_config(cls, resource_dir: str, server_config_class_name: str):
        """
        初始化配置，从配置文件中获取
        """
        bootstrap_file = PathUtil.join_path(resource_dir, "bootstrap.yaml", check_exist=True)
        container.config.from_yaml(bootstrap_file)
        cls._override_config_from_env()
        cls._init_config_from_server(server_config_class_name)

    @classmethod
    def _override_config_from_env(cls):
        """
        从环境变量覆盖文件配置
        """
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
    def _update_config_and_bean(cls, config: dict, *args, **kwargs):
        """
        更新配置
        :param config: 配置
        """
        config: str = config.get("content")
        new_config = providers.Configuration()
        new_config.from_dict(yaml.safe_load(config))
        container.config, old_config = new_config, container.config
        update_component_set = set()
        with cls._condition:
            try:
                cls._lock.acquire()
                for clazz, refresh_key_list in container.refresh_scope.kwargs.items():
                    for refresh_key in refresh_key_list:
                        new_config_val = new_config.get(refresh_key)
                        old_config_val = old_config.get(refresh_key)
                        if new_config_val != old_config_val:
                            update_component_set.add(clazz)
                            break
                for clazz in update_component_set:
                    logger.info(f"组件[{clazz}]更新")
                    provider_bean = container.providers.get(cls.get_name_from_class(clazz))
                    if isinstance(provider_bean, BaseSingleton):  # 单例才更新
                        provider_bean.reset()
                        cls._resolve_rv_dependent(clazz, update_component_set)
            finally:
                cls._lock.release()
                cls._condition.notify_all()

    @classmethod
    def _resolve_rv_dependent(cls, clazz: Type[T], update_component_set: set):
        """
        依赖组件更新，更新引用此组件的组件
        """
        rv_dependent_set = container.rv_dependent_dict.kwargs.get(clazz) or []
        for rv_dependent_cls in rv_dependent_set:
            if rv_dependent_cls not in update_component_set:
                logger.info(f"更新组件[{clazz}]的关联组件[{rv_dependent_cls}]")
                provider_bean = container.providers.get(cls.get_name_from_class(rv_dependent_cls))
                if isinstance(provider_bean, BaseSingleton):  # 单例才更新
                    provider_bean.reset()
                cls._resolve_rv_dependent(rv_dependent_cls, update_component_set)

    @classmethod
    def autowired(cls, name: str | Type[T]) -> T:
        """
        获取bean
        :param name: bean name or class
        :return: bean
        """
        cls._wait_for_lock()
        name = cls.get_name_from_class(name)
        try:
            bean = container.providers.get(name)()
            return bean
        except AttributeError:
            raise ValueError(f"bean [{name}] is not found")

    @classmethod
    def get_bean_func(cls, name: str | Type[T]):
        """
        返回一个获取bean的方法，用于FastAPI调用注入参数
        """

        def wrapper():
            return cls.autowired(name)

        return wrapper

    @classmethod
    def get_config_value(cls, key: str, required: bool = False):
        """
        获取配置值
        :param key: 配置key
        :param required: 是否必须
        :return: 配置值
        """
        cls._wait_for_lock()
        try:
            val = container.config.get(key, required=required)
        except Error as e:
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

    @classmethod
    def _wait_for_lock(cls):
        if cls._lock.locked():
            with cls._condition:
                pass


class Autowired[T]:
    """
    自动将定义的Bean添加至类__init__方法中，以实现自动注入，使用方法为
    在类中定义属性即可，示例如下:
    class A:
        redis_util: RedisUtil = Autowired()

    参数:
    name: 注册组件时的名称，可以为组件类本身，如果没有则使用类名(首字母小写)作为名称
    """

    def __init__(self, name: str | Type[T] = None):
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

    def __init__(self, name: str = None, singleton=True):
        self.name = name
        self.singleton = singleton

    def __call__(self, cls: Type[T], *args, **kwargs) -> Type[T]:
        if not self.name:
            self.name = ContainerUtil.get_name_from_class(cls)
        if self.name in container.providers:
            raise ValueError(f"bean name [{self.name}] is already exists")
        provider_type = providers.Factory
        if self.singleton:
            provider_type = providers.ThreadSafeSingleton
        attr_type_dict = get_type_hints(cls)
        origin_init = cls.__init__

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
