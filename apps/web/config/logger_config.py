from apps.base.config.logger_config import BaseLoggerConfig
from apps.web.utils.path_util import PathUtil


class LoggerConfig(BaseLoggerConfig):
    """Web 应用日志配置。"""

    RESOURCE_PATH = PathUtil.RESOURCE_PATH


LoggerConfig.init()
logger = LoggerConfig.get_logger()
