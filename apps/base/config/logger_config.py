import logging
import logging.config
from pathlib import Path
from typing import Any

import yaml


class BaseLoggerConfig:
    """应用日志配置基类。"""

    CONFIG_FILE_NAME = "logger_config.yaml"
    ROOT_PATH = Path(__file__).resolve().parents[3]
    RESOURCE_PATH: Path
    config: dict[str, Any]
    _cached = False

    @classmethod
    def init(cls) -> None:
        """初始化应用日志配置并创建文件日志目录。

        :return: None。
        """
        config_path = cls.RESOURCE_PATH / cls.CONFIG_FILE_NAME
        with config_path.open("r", encoding="utf-8") as file:
            cls.config = yaml.safe_load(file)
        cls._resolve_file_handler_paths()
        logging.config.dictConfig(cls.config)
        cls._cached = True

    @classmethod
    def _resolve_file_handler_paths(cls) -> None:
        """解析文件日志绝对路径并创建父目录。

        :return: None。
        """
        for handler in cls.config.get("handlers", {}).values():
            filename = handler.get("filename")
            if not filename:
                continue
            log_path = Path(filename)
            if not log_path.is_absolute():
                log_path = cls.ROOT_PATH / log_path
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handler["filename"] = str(log_path)

    @classmethod
    def get_config(cls) -> dict[str, Any]:
        """获取应用日志配置。

        :return: 日志配置字典。
        """
        if not cls._cached:
            cls.init()
        return cls.config

    @classmethod
    def get_logger(cls, name: str = __name__) -> logging.Logger:
        """获取日志记录器。

        :param name: 日志记录器名称。
        :return: 日志记录器。
        """
        return logging.getLogger(name)
