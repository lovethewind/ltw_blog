from apps.admin.dao.website_dao import AdminWebsiteDao
from apps.admin.dto.website_dto import AdminWebsiteDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.status_vo import AdminCheckStatusVO
from apps.admin.vo.website_vo import AdminWebsiteCreateVO, AdminWebsiteQueryVO, AdminWebsiteUpdateVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException


@Component()
class AdminWebsiteService(AdminBaseService):
    """后台网站导航服务。"""

    admin_website_dao: AdminWebsiteDao = Autowired()

    async def list_websites(self, query_vo: AdminWebsiteQueryVO) -> dict:
        """
        分页查询网站导航。

        :param query_vo: 网站导航查询参数
        :return: 网站导航分页数据
        """
        websites, total = await self.admin_website_dao.list_websites(
            query_vo.current, query_vo.size, query_vo.keyword, query_vo.category_id, query_vo.status, query_vo.user_id
        )
        records = [AdminWebsiteDTO.model_validate(website) for website in websites]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_website(self, website_id: int) -> AdminWebsiteDTO:
        """
        查询网站导航详情。

        :param website_id: 网站导航 ID
        :return: 网站导航详情
        :raises MyException: 网站导航不存在时抛出
        """
        website = await self.admin_website_dao.get_website_by_id(website_id)
        if not website:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminWebsiteDTO.model_validate(website)

    async def create_website(self, website_vo: AdminWebsiteCreateVO) -> AdminWebsiteDTO:
        """
        创建网站导航。

        :param website_vo: 网站导航创建参数
        :return: 网站导航详情
        """
        data = website_vo.model_dump(exclude_none=True)
        self._normalize_website_data(data)
        website = await self.admin_website_dao.create_website(data)
        return AdminWebsiteDTO.model_validate(website)

    async def update_website(self, website_id: int, website_vo: AdminWebsiteUpdateVO) -> AdminWebsiteDTO:
        """
        更新网站导航。

        :param website_id: 网站导航 ID
        :param website_vo: 网站导航更新参数
        :return: 网站导航详情
        :raises MyException: 网站导航不存在时抛出
        """
        website = await self.admin_website_dao.get_website_by_id(website_id)
        if not website:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = website_vo.model_dump(exclude_none=True)
        self._normalize_website_data(data)
        website = await self.admin_website_dao.update_website(website, data)
        return AdminWebsiteDTO.model_validate(website)

    async def update_website_status(self, website_id: int, status_vo: AdminCheckStatusVO) -> AdminWebsiteDTO:
        """
        更新网站导航审核状态。

        :param website_id: 网站导航 ID
        :param status_vo: 审核状态参数
        :return: 网站导航详情
        :raises MyException: 网站导航不存在时抛出
        """
        website = await self.admin_website_dao.get_website_by_id(website_id)
        if not website:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        website = await self.admin_website_dao.update_website(website, {"status": status_vo.status})
        return AdminWebsiteDTO.model_validate(website)

    async def delete_website(self, website_id: int) -> None:
        """
        删除网站导航。

        :param website_id: 网站导航 ID
        :return: None
        :raises MyException: 网站导航不存在时抛出
        """
        website = await self.admin_website_dao.get_website_by_id(website_id)
        if not website:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_website_dao.delete_website(website_id)

    def _normalize_website_data(self, data: dict[str, object]) -> None:
        """
        规范化网站导航保存数据。

        :param data: 网站导航数据
        :return: None
        """
        for field in ("cover", "introduce"):
            if field in data and data[field] is None:
                data[field] = ""
