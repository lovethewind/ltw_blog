import asyncio
import os
import threading
from typing import Any, Callable
from urllib.parse import urlparse

import yaml
from v2.nacos import ClientConfigBuilder, ConfigParam, GRPCConfig, NacosConfigService

from apps.base.core.depend_inject import Component, Value

APP_ENV_ACTIVE_NAME = "app.active"
APP_NAME = "app.name"


@Component()
class NacosConfig:
    server_addr: str = Value("nacos.server-addr")
    namespace: str = Value("nacos.namespace")
    username: str = Value("nacos.username")
    password: str = Value("nacos.password")
    group: str = Value("nacos.group")
    file_extension: str = Value("nacos.file-extension")
    app_name: str = Value(APP_NAME)
    app_env: str = Value(APP_ENV_ACTIVE_NAME)

    def __init__(self) -> None:
        """
        初始化 Nacos 配置客户端。

        :return: None
        """
        self.data_id = f"{self.app_name}-{self.app_env}.{self.file_extension}"
        add_no_proxy_host(self.server_addr)
        self.client = LatestNacosConfigClient(
            server_addr=self.server_addr,
            namespace=self.namespace,
            username=self.username,
            password=self.password,
        )

    def get_config(self) -> dict:
        """
        获取当前应用配置。

        :return: Nacos 中的 YAML 配置字典
        """
        config = self.client.get_config(self.data_id, self.group)
        config = yaml.safe_load(config)
        return config

    def add_watcher(self, watcher: Callable[..., Any]) -> None:
        """
        监听当前应用配置变更。

        :param watcher: 配置变更回调函数
        :return: None
        """
        self.client.add_watcher(self.data_id, self.group, watcher)

    def __str__(self) -> str:
        """
        返回当前配置 dataId。

        :return: 当前配置 dataId
        """
        return self.data_id


class LatestNacosConfigClient:
    """最新版 Nacos Python SDK 的同步适配器。"""

    def __init__(self, server_addr: str, namespace: str, username: str, password: str) -> None:
        """
        初始化最新版 Nacos SDK 客户端。

        :param server_addr: Nacos 服务地址
        :param namespace: Nacos 命名空间
        :param username: Nacos 用户名
        :param password: Nacos 密码
        :return: None
        """
        self.server_addr = server_addr
        self.namespace = namespace
        self.username = username
        self.password = password
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.client = self._run_async(self._create_client())

    def get_config(self, data_id: str, group: str) -> str:
        """
        同步获取 Nacos 配置。

        :param data_id: 配置 dataId
        :param group: 配置分组
        :return: 配置内容
        """
        return self._run_async(self.client.get_config(ConfigParam(data_id=data_id, group=group)))

    def add_watcher(self, data_id: str, group: str, watcher: Callable[..., Any]) -> None:
        """
        同步添加 Nacos 配置监听。

        :param data_id: 配置 dataId
        :param group: 配置分组
        :param watcher: 项目配置变更回调函数
        :return: None
        """

        async def listener(tenant: str, group_name: str, config_data_id: str, content: str) -> None:
            """
            将最新版 SDK 回调参数转换为项目旧回调结构。

            :param tenant: Nacos 命名空间
            :param group_name: 配置分组
            :param config_data_id: 配置 dataId
            :param content: 配置内容
            :return: None
            """
            watcher(
                {
                    "tenant": tenant,
                    "group": group_name,
                    "dataId": config_data_id,
                    "content": content,
                }
            )

        self._run_async(self.client.add_listener(data_id, group, listener))

    async def _create_client(self) -> NacosConfigService:
        """
        创建最新版 Nacos 配置服务客户端。

        :return: Nacos 配置服务客户端
        """
        config = (
            ClientConfigBuilder()
            .server_address(self.server_addr)
            .namespace_id(self.namespace)
            .username(self.username)
            .password(self.password)
            .log_dir("./logs/nacos")
            .cache_dir("./nacos-data/cache")
            .grpc_config(GRPCConfig(grpc_timeout=5000))
            .build()
        )
        return await NacosConfigService.create_config_service(config)

    def _run_loop(self) -> None:
        """
        运行最新版 SDK 所需的后台事件循环。

        :return: None
        """
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _run_async(self, coroutine: Any) -> Any:
        """
        在线程事件循环中同步等待异步任务完成。

        :param coroutine: 待执行的协程
        :return: 协程执行结果
        """
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        return future.result()


def add_no_proxy_host(server_addr: str) -> None:
    """
    将 Nacos 地址加入代理绕过列表。

    :param server_addr: Nacos 服务地址，多个地址使用英文逗号分隔
    :return: None
    """
    hosts = {"localhost", "127.0.0.1", "::1"}
    for item in server_addr.split(","):
        item = item.strip()
        if not item:
            continue
        parsed = urlparse(item if "://" in item else f"http://{item}")
        if parsed.hostname:
            hosts.add(parsed.hostname)
    for key in ("NO_PROXY", "no_proxy"):
        exists_hosts = {host.strip() for host in os.environ.get(key, "").split(",") if host.strip()}
        os.environ[key] = ",".join(sorted(exists_hosts | hosts))
