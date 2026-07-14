from apps.admin.dao.config_dao import AdminConfigDao
from apps.admin.dto.config_dto import AdminConfigDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.config_vo import AdminConfigCreateVO, AdminConfigQueryVO, AdminConfigUpdateVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException


@Component()
class AdminConfigService(AdminBaseService):
    """后台配置服务。"""

    admin_config_dao: AdminConfigDao = Autowired()

    async def list_configs(self, query_vo: AdminConfigQueryVO) -> dict:
        """
        分页查询配置。

        :param query_vo: 配置查询参数
        :return: 配置分页数据
        """
        configs, total = await self.admin_config_dao.list_configs(
            query_vo.current, query_vo.size, query_vo.keyword, query_vo.is_active
        )
        records = AdminConfigDTO.bulk_model_validate(configs)
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_config(self, config_id: int) -> AdminConfigDTO:
        """
        查询配置详情。

        :param config_id: 配置 ID
        :return: 配置详情
        :raises MyException: 配置不存在时抛出
        """
        config = await self.admin_config_dao.get_config_by_id(config_id)
        if not config:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminConfigDTO.model_validate(config)

    async def create_config(self, config_vo: AdminConfigCreateVO) -> AdminConfigDTO:
        """
        创建配置。

        :param config_vo: 配置创建参数
        :return: 配置详情
        """
        data = config_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        config = await self.admin_config_dao.create_config(data)
        return AdminConfigDTO.model_validate(config)

    async def update_config(self, config_id: int, config_vo: AdminConfigUpdateVO) -> AdminConfigDTO:
        """
        更新配置。

        :param config_id: 配置 ID
        :param config_vo: 配置更新参数
        :return: 配置详情
        :raises MyException: 配置不存在时抛出
        """
        config = await self.admin_config_dao.get_config_by_id(config_id)
        if not config:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = config_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        config = await self.admin_config_dao.update_config(config, data)
        return AdminConfigDTO.model_validate(config)

    async def delete_config(self, config_id: int) -> None:
        """
        删除配置。

        :param config_id: 配置 ID
        :return: None
        :raises MyException: 配置不存在时抛出
        """
        config = await self.admin_config_dao.get_config_by_id(config_id)
        if not config:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_config_dao.delete_config(config_id)
