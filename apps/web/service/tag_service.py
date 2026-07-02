# @Time    : 2024/8/23 14:37
# @Author  : frank
# @File    : category_service.py

from apps.base.core.depend_inject import Component
from apps.base.enum.category import TagLevelEnum
from apps.base.models.category import Tag
from apps.web.dto.category_dto import TagDTO
from apps.web.vo.tag_vo import TagCreateVO


@Component()
class TagService:

    async def create_or_get(self, tag_vo: TagCreateVO) -> dict:
        """
        创建未分组的展示层标签，同名标签已存在时直接复用。

        :param tag_vo: 自定义标签创建参数。
        :return: 创建或复用的标签详情。
        """
        tag_name = " ".join(tag_vo.name.split())
        tag = await Tag.filter(name__iexact=tag_name, level=TagLevelEnum.SHOW).first()
        if not tag:
            tag = await Tag.create(
                name=tag_name,
                description="",
                parent_id=0,
                level=TagLevelEnum.SHOW,
                is_active=True,
            )
        return TagDTO.model_validate(tag, from_attributes=True).model_dump(by_alias=True, exclude={"children"})

    async def find_all(self):
        """
        获取树形节点和所有
        :return:
        """
        tag_list = await Tag.filter(is_active=True)
        tags = self._build_tree(tag_list)
        tag_list = TagDTO.bulk_model_validate(tag_list)
        ret = {"nodes": tags, "records": tag_list}
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
