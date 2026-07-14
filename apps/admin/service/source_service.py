from apps.admin.dao.source_dao import AdminSourceDao
from apps.admin.dto.source_dto import AdminSourceDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.source_vo import AdminSourceQueryVO, AdminSourceUpdateVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.utils.oss_util import OssUtil


@Component()
class AdminSourceService(AdminBaseService):
    """后台资源服务。"""

    admin_source_dao: AdminSourceDao = Autowired()
    oss_util: OssUtil = Autowired()

    async def list_sources(self, query_vo: AdminSourceQueryVO) -> dict:
        """
        分页查询资源。

        :param query_vo: 资源查询参数
        :return: 资源分页数据
        """
        sources, total = await self.admin_source_dao.list_sources(
            query_vo.current, query_vo.size, query_vo.keyword, query_vo.user_id, query_vo.is_deleted
        )
        records = AdminSourceDTO.bulk_model_validate(sources)
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def update_source(self, source_id: int, source_vo: AdminSourceUpdateVO) -> AdminSourceDTO:
        """
        更新资源。

        :param source_id: 资源 ID
        :param source_vo: 资源更新参数
        :return: 资源详情
        :raises MyException: 资源不存在时抛出
        """
        source = await self.admin_source_dao.get_source_by_id(source_id)
        if not source:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        source = await self.admin_source_dao.update_source(source, source_vo.model_dump(exclude_none=True))
        return AdminSourceDTO.model_validate(source)

    async def delete_source(self, source_id: int) -> None:
        """
        永久删除已标记资源及其 OSS 文件。

        :param source_id: 资源 ID
        :return: None
        :raises MyException: 资源不存在或尚未标记删除时抛出
        """
        source = await self.admin_source_dao.get_source_by_id(source_id)
        if not source:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        if not source.is_deleted:
            raise MyException.param_err("请先将资源标记为已删除")
        await self.oss_util.delete_file(source.url)
        await self.admin_source_dao.delete_source(source_id)
