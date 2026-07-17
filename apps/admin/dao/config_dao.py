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

    async def get_configs_by_names(self, names: list[str]) -> dict[str, Config]:
        """
        按配置键批量查询最新配置。

        :param names: 配置键列表。
        :return: 配置键到配置对象的映射。
        """
        if not names:
            return {}
        configs = await db.model_all(select(Config).where(Config.name.in_(names)).order_by(Config.id.desc()))
        result: dict[str, Config] = {}
        for config in configs:
            result.setdefault(config.name, config)
        return result

    async def save_named_configs(self, configs: dict[str, tuple[str, str]]) -> None:
        """
        在同一事务中新增或更新一组具名配置。

        :param configs: 配置键到“配置值、说明”的映射。
        :return: None。
        """
        if not configs:
            return
        async with db.atomic() as session:
            existing_records = await session.scalars(
                select(Config).where(Config.name.in_(configs.keys())).order_by(Config.id.desc())
            )
            existing = {record.name: record for record in existing_records}
            for name, (value, description) in configs.items():
                config = existing.get(name)
                if config:
                    config.value = value
                    config.description = description
                    config.is_active = True
                else:
                    session.add(Config(name=name, value=value, description=description, is_active=True))

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
