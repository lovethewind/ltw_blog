from apps.admin.utils.path_util import AdminPathUtil
from apps.base.config.logger_config import BaseLoggerConfig


class LoggerConfig(BaseLoggerConfig):
    """后台管理应用日志配置。"""

    RESOURCE_PATH = AdminPathUtil.RESOURCE_PATH


LoggerConfig.init()
logger = LoggerConfig.get_logger()
