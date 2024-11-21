# @Time    : 2024/8/23 14:37
# @Author  : frank
# @File    : category_service.py

from apps.base.core.depend_inject import Component, Autowired
from apps.base.models.category import Category
from apps.web.dao.category_dao import CategoryDao
from apps.web.dto.category_dto import CategoryDTO


@Component()
class CategoryService:
    category_dao: CategoryDao = Autowired()

    async def find_all(self):
        """
        查询出所有分类
        :return:
        """
        category_list = await Category.filter(is_active=True)
        ret = []
        category_article_count_dict = await self.category_dao.get_category_article_count()
        for category in category_list:
            dto = CategoryDTO.model_validate(category, from_attributes=True)
            dto.article_count = category_article_count_dict.get(category.id, 0)
            ret.append(dto)
        return ret
