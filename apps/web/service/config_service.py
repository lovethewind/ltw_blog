import hashlib
from datetime import datetime

from sqlalchemy import select

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.dto.search_analysis_dto import SearchAnalysisConfigDTO
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

    async def get_published_search_analysis(self) -> SearchAnalysisConfigDTO:
        """
        获取已发布搜索分词配置。

        :return: 已发布配置；不存在或格式错误时返回默认配置。
        """
        stmt = (
            select(Config)
            .where(Config.name == "search.analysis.published", Config.is_active.is_(True))
            .order_by(Config.id.desc())
        )
        config = await db.model_first(stmt)
        if not config:
            return SearchAnalysisConfigDTO()
        try:
            return SearchAnalysisConfigDTO.model_validate_json(config.value)
        except ValueError:
            return SearchAnalysisConfigDTO()

    async def get_search_analysis_dictionary(self, dictionary_type: str) -> tuple[str, str, datetime]:
        """
        获取 IK 远程词库正文和缓存版本信息。

        :param dictionary_type: 词库类型，支持 custom 和 stop。
        :return: 词库正文、ETag 和最后更新时间。
        :raises MyException: 词库类型不支持时抛出。
        """
        if dictionary_type not in {"custom", "stop"}:
            raise MyException(ErrorCode.PARAM_ERROR)
        stmt = (
            select(Config)
            .where(Config.name == "search.analysis.published", Config.is_active.is_(True))
            .order_by(Config.id.desc())
        )
        record = await db.model_first(stmt)
        try:
            config = SearchAnalysisConfigDTO.model_validate_json(record.value) if record else SearchAnalysisConfigDTO()
        except ValueError:
            config = SearchAnalysisConfigDTO()
        words = config.custom_words if dictionary_type == "custom" else config.stop_words
        content = "".join(f"{word}\n" for word in words)
        checksum = hashlib.sha256(f"{config.version}:{dictionary_type}:{content}".encode()).hexdigest()[:24]
        updated_at = record.update_time if record else datetime(1970, 1, 1)
        return content, f'"{checksum}"', updated_at
