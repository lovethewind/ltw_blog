import logging
import logging.config
import os

import yaml

from apps.web.utils.path_util import PathUtil


class LoggerConfig:
    """
    日志配置
    """
    CONFIG_FILE_NAME = "logger_config.yaml"
    config: dict
    _cached = False

    @classmethod
    def init(cls):
        os.makedirs(PathUtil.PROJECT_PATH / "logs", exist_ok=True)
        with open(PathUtil.get_resource_path(cls.CONFIG_FILE_NAME), "r", encoding="utf-8") as f:
            cls.config = yaml.safe_load(f)
        logging.config.dictConfig(cls.config)
        cls._cached = True

    @classmethod
    def get_config(cls):
        if not cls._cached:
            cls.init()
            cls._cached = True
        return cls.config

    @classmethod
    def get_logger(cls, name: str = __name__):
        return logging.getLogger(name)


LoggerConfig.init()
logger = LoggerConfig.get_logger()
