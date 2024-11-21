from typing import Any, Callable

import yaml

from apps.base.core.depend_inject import Value, Component
from apps.web.core.nacos import NacosClient

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

    def __init__(self, ):
        self.data_id = f"{self.app_name}-{self.app_env}.{self.file_extension}"
        self.client = NacosClient(self.server_addr, namespace=self.namespace,
                                  username=self.username, password=self.password)

    def get_config(self) -> dict:
        config = self.client.get_config(self.data_id, self.group)
        config = yaml.safe_load(config)
        return config

    def add_watcher(self, watcher: Callable[..., Any]):
        self.client.add_config_watcher(self.data_id, self.group, watcher)

    def __str__(self):
        return self.data_id
