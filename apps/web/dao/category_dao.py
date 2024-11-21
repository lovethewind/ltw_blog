# @Time    : 2024/8/23 14:44
# @Author  : frank
# @File    : category_dao.py
from tortoise.functions import Count

from apps.base.core.depend_inject import Component
from apps.base.models.article import Article


@Component()
class CategoryDao:

    async def get_category_article_count(self) -> dict:
        """
        获取各个分类下的文章数量
        :return:
        """
        info_list = await Article.annotate(count=Count("id")).group_by("category_id").values("category_id", "count")
        info_dict = {item["category_id"]: item["count"] for item in info_list}
        return info_dict
