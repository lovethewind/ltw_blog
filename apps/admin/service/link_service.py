from apps.admin.dao.link_dao import AdminLinkDao
from apps.admin.dto.link_dto import AdminLinkDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.link_vo import AdminLinkCreateVO, AdminLinkQueryVO, AdminLinkUpdateVO
from apps.admin.vo.status_vo import AdminCheckStatusVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException


@Component()
class AdminLinkService(AdminBaseService):
    """后台友链服务。"""

    admin_link_dao: AdminLinkDao = Autowired()

    async def list_links(self, query_vo: AdminLinkQueryVO) -> dict:
        """
        分页查询友链。

        :param query_vo: 友链查询参数
        :return: 友链分页数据
        """
        links, total = await self.admin_link_dao.list_links(
            query_vo.current, query_vo.size, query_vo.keyword, query_vo.status
        )
        records = AdminLinkDTO.bulk_model_validate(links)
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_link(self, link_id: int) -> AdminLinkDTO:
        """
        查询友链详情。

        :param link_id: 友链 ID
        :return: 友链详情
        :raises MyException: 友链不存在时抛出
        """
        link = await self.admin_link_dao.get_link_by_id(link_id)
        if not link:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminLinkDTO.model_validate(link)

    async def create_link(self, link_vo: AdminLinkCreateVO) -> AdminLinkDTO:
        """
        创建友链。

        :param link_vo: 友链创建参数
        :return: 友链详情
        """
        data = link_vo.model_dump(exclude_none=True)
        self._normalize_link_data(data)
        link = await self.admin_link_dao.create_link(data)
        return AdminLinkDTO.model_validate(link)

    async def update_link(self, link_id: int, link_vo: AdminLinkUpdateVO) -> AdminLinkDTO:
        """
        更新友链。

        :param link_id: 友链 ID
        :param link_vo: 友链更新参数
        :return: 友链详情
        :raises MyException: 友链不存在时抛出
        """
        link = await self.admin_link_dao.get_link_by_id(link_id)
        if not link:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = link_vo.model_dump(exclude_none=True)
        self._normalize_link_data(data)
        link = await self.admin_link_dao.update_link(link, data)
        return AdminLinkDTO.model_validate(link)

    async def update_link_status(self, link_id: int, status_vo: AdminCheckStatusVO) -> AdminLinkDTO:
        """
        更新友链审核状态。

        :param link_id: 友链 ID
        :param status_vo: 审核状态参数
        :return: 友链详情
        :raises MyException: 友链不存在时抛出
        """
        link = await self.admin_link_dao.get_link_by_id(link_id)
        if not link:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        link = await self.admin_link_dao.update_link(link, {"status": status_vo.status})
        return AdminLinkDTO.model_validate(link)

    async def delete_link(self, link_id: int) -> None:
        """
        删除友链。

        :param link_id: 友链 ID
        :return: None
        :raises MyException: 友链不存在时抛出
        """
        link = await self.admin_link_dao.get_link_by_id(link_id)
        if not link:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_link_dao.delete_link(link_id)

    def _normalize_link_data(self, data: dict[str, object]) -> None:
        """
        规范化友链保存数据。

        :param data: 友链数据
        :return: None
        """
        for field in ("cover", "description", "introduce"):
            if field in data and data[field] is None:
                data[field] = ""
