from apps.base.config.logger_config import BaseLoggerConfig
from apps.scheduler.utils.path_util import SchedulerPathUtil


class LoggerConfig(BaseLoggerConfig):
    """定时任务服务日志配置。"""

    RESOURCE_PATH = SchedulerPathUtil.RESOURCE_PATH


LoggerConfig.init()
logger = LoggerConfig.get_logger()
