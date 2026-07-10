from apps.admin.utils.path_util import AdminPathUtil
from apps.base.core.depend_inject import ContainerUtil, GetValue
from apps.web.config.nacos_config import NacosConfig

_container_initialized = False


def init_container_config() -> None:
    """
    初始化后台管理应用配置容器。

    :return: None
    """
    global _container_initialized
    if _container_initialized:
        return
    ContainerUtil.init(resource_dir=AdminPathUtil.RESOURCE_PATH, server_config_class=NacosConfig)
    _container_initialized = True


def get_server_host() -> str:
    """
    获取后台管理服务监听地址。

    :return: 服务监听地址
    """
    init_container_config()
    return GetValue("app.server.host")


def get_server_port() -> int:
    """
    获取后台管理服务监听端口。

    :return: 服务监听端口
    """
    init_container_config()
    return int(GetValue("app.server.port"))


def get_server_bind() -> str:
    """
    获取后台管理 Gunicorn 服务绑定地址。

    :return: Gunicorn 绑定地址
    """
    return f"{get_server_host()}:{get_server_port()}"
