from apps.base.core.depend_inject import ContainerUtil
from apps.scheduler.config.nacos_config import NacosConfig
from apps.scheduler.utils.path_util import SchedulerPathUtil

_container_initialized = False


def init_container_config() -> None:
    """初始化定时任务服务配置容器。

    :return: None。
    """
    global _container_initialized
    if _container_initialized:
        return
    ContainerUtil.init(
        resource_dir=SchedulerPathUtil.RESOURCE_PATH,
        server_config_class=NacosConfig,
        server_config_class_name="schedulerNacosConfig",
    )
    _container_initialized = True
