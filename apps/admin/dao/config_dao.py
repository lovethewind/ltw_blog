from typing import Any

from sqlalchemy import or_, select

from apps.admin.dao.base_dao import _create, _delete, _paginate, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.config import Config


@Component()
class AdminConfigDao:
    """后台配置数据访问对象。"""

    async def list_configs(
        self, current: int, size: int, keyword: str | None = None, is_active: bool | None = None
    ) -> tuple[list[Config], int]:
        """
        分页查询配置。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 配置关键词。
        :param is_active: 是否启用。
        :return: 配置列表和总数。
        """
        stmt = select(Config)
        if keyword:
            stmt = stmt.where(or_(Config.name.ilike(f"%{keyword}%"), Config.description.ilike(f"%{keyword}%")))
        if is_active is not None:
            stmt = stmt.where(Config.is_active == is_active)
        return await _paginate(stmt, current, size, Config.id.desc())

    async def get_config_by_id(self, config_id: int) -> Config | None:
        """
        根据 ID 查询配置。

        :param config_id: 配置 ID。
        :return: 配置对象。
        """
        return await db.model_first(select(Config).where(Config.id == config_id))

    async def create_config(self, data: dict[str, Any]) -> Config:
        """
        创建配置。

        :param data: 配置数据。
        :return: 配置对象。
        """
        return await _create(Config, data)

    async def update_config(self, config: Config, data: dict[str, Any]) -> Config:
        """
        更新配置。

        :param config: 配置对象。
        :param data: 更新数据。
        :return: 配置对象。
        """
        return await _update(config, data)

    async def delete_config(self, config_id: int) -> None:
        """
        删除配置。

        :param config_id: 配置 ID。
        :return: None。
        """
        await _delete(Config, config_id)
