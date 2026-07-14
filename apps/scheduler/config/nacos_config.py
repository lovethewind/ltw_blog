from apps.base.config.nacos_config import BaseNacosConfig
from apps.base.core.depend_inject import Component


@Component("schedulerNacosConfig")
class NacosConfig(BaseNacosConfig):
    """定时任务服务 Nacos 配置客户端。"""
