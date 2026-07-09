from sqlalchemy import select

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.config import Config


@Component()
class ConfigService:
    async def get_config(self, key: str) -> str:
        """
        根据 key 获取启用配置值。

        :param key: 配置键。
        :return: 配置值。
        """
        stmt = select(Config).where(Config.name == key, Config.is_active.is_(True))
        config = await db.model_first(stmt)
        if not config:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return config.value
