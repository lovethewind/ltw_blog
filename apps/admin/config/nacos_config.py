from apps.base.config.nacos_config import BaseNacosConfig
from apps.base.core.depend_inject import Component


@Component("adminNacosConfig")
class NacosConfig(BaseNacosConfig):
    """后台管理 Nacos 配置客户端。"""
