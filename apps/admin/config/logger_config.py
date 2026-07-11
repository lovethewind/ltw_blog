import logging
import logging.config
import os

import yaml

from apps.admin.utils.path_util import AdminPathUtil


class LoggerConfig:
    """
    日志配置
    """

    CONFIG_FILE_NAME = "logger_config.yaml"
    config: dict
    _cached = False

    @classmethod
    def init(cls) -> None:
        """
        初始化后台管理日志配置。

        :return: None。
        """
        os.makedirs(AdminPathUtil.PROJECT_PATH / "logs", exist_ok=True)
        with open(AdminPathUtil.get_resource_path(cls.CONFIG_FILE_NAME), "r", encoding="utf-8") as f:
            cls.config = yaml.safe_load(f)
        logging.config.dictConfig(cls.config)
        cls._cached = True

    @classmethod
    def get_config(cls) -> dict:
        """
        获取后台管理日志配置。

        :return: 日志配置字典。
        """
        if not cls._cached:
            cls.init()
            cls._cached = True
        return cls.config

    @classmethod
    def get_logger(cls, name: str = __name__) -> logging.Logger:
        """
        获取后台管理日志记录器。

        :param name: 日志记录器名称。
        :return: 日志记录器。
        """
        return logging.getLogger(name)


LoggerConfig.init()
logger = LoggerConfig.get_logger()
