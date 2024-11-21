# @Time    : 2024/8/23 14:37
# @Author  : frank
# @File    : category_service.py

from apps.base.core.depend_inject import Component
from apps.base.enum.category import TagLevelEnum
from apps.base.models.category import Tag
from apps.web.dto.category_dto import TagDTO


@Component()
class TagService:

    async def find_all(self):
        """
        获取树形节点和所有
        :return:
        """
        tag_list = await Tag.filter(is_active=True)
        tags = self._build_tree(tag_list)
        tag_list = TagDTO.bulk_model_validate(tag_list)
        ret = {
            "nodes": tags,
            "records": tag_list
        }
        return ret

    def _build_tree(self, tag_list: list[Tag]) -> list[TagDTO]:
        trees = []
        for tag in tag_list:
            if tag.level == TagLevelEnum.CATEGORY:  # 分类层找到下面的展示层
                trees.append(self._find_children(tag, tag_list))
        return trees

    def _find_children(self, tag: Tag, tag_list: list[Tag]) -> TagDTO:
        dto = TagDTO.model_validate(tag, from_attributes=True)
        for m in tag_list:
            if tag.id == m.parent_id:
                dto.children.append(self._find_children(m, tag_list))
        return dto
