from apps.admin.dao.website_category_dao import AdminWebsiteCategoryDao
from apps.admin.dto.website_category_dto import AdminWebsiteCategoryDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.website_category_vo import AdminWebsiteCategoryCreateVO, AdminWebsiteCategoryUpdateVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException


@Component()
class AdminWebsiteCategoryService(AdminBaseService):
    """后台网站导航分类服务。"""

    admin_website_category_dao: AdminWebsiteCategoryDao = Autowired()

    async def list_website_categories(self) -> list[AdminWebsiteCategoryDTO]:
        """
        查询网站导航分类列表。

        :return: 网站导航分类列表
        """
        categories = await self.admin_website_category_dao.list_website_categories()
        return AdminWebsiteCategoryDTO.bulk_model_validate(categories)

    async def create_website_category(self, category_vo: AdminWebsiteCategoryCreateVO) -> AdminWebsiteCategoryDTO:
        """
        创建网站导航分类。

        :param category_vo: 网站导航分类创建参数
        :return: 网站导航分类详情
        """
        category = await self.admin_website_category_dao.create_website_category(
            category_vo.model_dump(exclude_none=True)
        )
        return AdminWebsiteCategoryDTO.model_validate(category)

    async def update_website_category(
        self, category_id: int, category_vo: AdminWebsiteCategoryUpdateVO
    ) -> AdminWebsiteCategoryDTO:
        """
        更新网站导航分类。

        :param category_id: 网站导航分类 ID
        :param category_vo: 网站导航分类更新参数
        :return: 网站导航分类详情
        :raises MyException: 网站导航分类不存在时抛出
        """
        category = await self.admin_website_category_dao.get_website_category_by_id(category_id)
        if not category:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        category = await self.admin_website_category_dao.update_website_category(
            category, category_vo.model_dump(exclude_none=True)
        )
        return AdminWebsiteCategoryDTO.model_validate(category)

    async def delete_website_category(self, category_id: int) -> None:
        """
        删除网站导航分类。

        :param category_id: 网站导航分类 ID
        :return: None
        :raises MyException: 网站导航分类不存在时抛出
        """
        category = await self.admin_website_category_dao.get_website_category_by_id(category_id)
        if not category:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_website_category_dao.delete_website_category(category_id)
