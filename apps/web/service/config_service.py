# @Time    : 2024/8/23 14:30
# @Author  : frank
# @File    : config_service.py
from apps.base.core.depend_inject import Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.config import Config


@Component()
class ConfigService:
    async def get_config(self, key: str) -> str:
        """
        根据key获取配置
        :param key:
        :return:
        """
        config = await Config.filter(name=key, is_active=True).first()
        if not config:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return config.value
