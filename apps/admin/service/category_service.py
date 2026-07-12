from apps.admin.dao.category_dao import AdminCategoryDao
from apps.admin.dto.category_dto import AdminCategoryDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.category_vo import AdminCategoryCreateVO, AdminCategoryUpdateVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException


@Component()
class AdminCategoryService(AdminBaseService):
    """后台分类服务。"""

    admin_category_dao: AdminCategoryDao = Autowired()

    async def list_categories(self) -> list[AdminCategoryDTO]:
        """
        查询分类列表。

        :return: 分类列表
        """
        categories = await self.admin_category_dao.list_categories()
        return [AdminCategoryDTO.model_validate(category) for category in categories]

    async def create_category(self, category_vo: AdminCategoryCreateVO) -> AdminCategoryDTO:
        """
        创建分类。

        :param category_vo: 分类创建参数
        :return: 分类详情
        """
        data = category_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        category = await self.admin_category_dao.create_category(data)
        return AdminCategoryDTO.model_validate(category)

    async def update_category(self, category_id: int, category_vo: AdminCategoryUpdateVO) -> AdminCategoryDTO:
        """
        更新分类。

        :param category_id: 分类 ID
        :param category_vo: 分类更新参数
        :return: 分类详情
        :raises MyException: 分类不存在时抛出
        """
        category = await self.admin_category_dao.get_category_by_id(category_id)
        if not category:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = category_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        category = await self.admin_category_dao.update_category(category, data)
        return AdminCategoryDTO.model_validate(category)

    async def delete_category(self, category_id: int) -> None:
        """
        删除分类。

        :param category_id: 分类 ID
        :return: None
        :raises MyException: 分类不存在时抛出
        """
        category = await self.admin_category_dao.get_category_by_id(category_id)
        if not category:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_category_dao.delete_category(category_id)
