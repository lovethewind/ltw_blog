import asyncio

from sqlalchemy import func, select

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.article import Article
from apps.base.models.category import Category
from apps.web.dto.category_dto import CategoryDTO


@Component()
class CategoryService:

    async def find_all(self) -> list[CategoryDTO]:
        """
        查询出所有启用分类，并填充分类文章数量。

        :return: 分类 DTO 列表。
        """
        qc = select(Category).where(Category.is_active.is_(True)).order_by(Category.id.desc())
        qg = select(Article.category_id, func.count(Article.id)).group_by(Article.category_id)
        category_list, category_article_count = await asyncio.gather(
            db.model_all(qc),
            db.all(qg),
        )
        ret = []
        category_article_count_dict = dict(category_article_count)
        for category in category_list:
            dto = CategoryDTO.model_validate(category, from_attributes=True)
            dto.article_count = category_article_count_dict.get(category.id, 0)
            ret.append(dto)
        return ret
