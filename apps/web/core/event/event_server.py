# @Time    : 2024/11/4 16:39
# @Author  : frank
# @File    : event_server.py
import asyncio
from inspect import iscoroutinefunction
from typing import Callable

from apps.web.config.logger_config import logger
from apps.web.core.event.event_name import EventName


class EventServer:
    _instance: "EventServer"

    def __init__(self):
        if hasattr(self, "_instance"):
            raise RuntimeError("单例模式不允许实例化多个对象")
        self.event_map: dict[str, list[Callable]] = {}

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def on(self, event_name: EventName, func: Callable):
        """
        注册事件
        :param event_name: 事件名称
        :param func: 事件处理函数
        :return:
        """
        if event_name not in self.event_map:
            self.event_map[event_name] = []
        if func in self.event_map[event_name]:
            return
        self.event_map[event_name].append(func)

    def emit(self, event_name: str, *args, **kwargs):
        """
        提交事件
        :param event_name: 事件名称
        :param args: 参数
        :param kwargs: 参数
        :return:
        """
        if event_name not in self.event_map:
            return
        for func in self.event_map[event_name]:
            try:
                if iscoroutinefunction(func):
                    asyncio.create_task(func(*args, **kwargs))
                    continue
                func(*args, **kwargs)
            except Exception as e:
                logger.error(f"事件 {event_name} 处理函数 {func.__name__} 执行失败，错误信息：{e}")
