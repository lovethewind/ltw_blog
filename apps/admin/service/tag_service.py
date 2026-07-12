from apps.admin.dao.tag_dao import AdminTagDao
from apps.admin.dto.tag_dto import AdminTagDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.tag_vo import AdminTagCreateVO, AdminTagUpdateVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.category import Tag


@Component()
class AdminTagService(AdminBaseService):
    """后台标签服务。"""

    admin_tag_dao: AdminTagDao = Autowired()

    async def list_tag_tree(self, active_only: bool = False) -> list[AdminTagDTO]:
        """
        查询标签树。

        :param active_only: 是否只查询启用标签
        :return: 标签树
        """
        tags = await self.admin_tag_dao.list_tags(active_only)
        return self._build_tag_tree(tags)

    async def create_tag(self, tag_vo: AdminTagCreateVO) -> AdminTagDTO:
        """
        创建标签。

        :param tag_vo: 标签创建参数
        :return: 标签详情
        """
        data = tag_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        tag = await self.admin_tag_dao.create_tag(data)
        return AdminTagDTO.model_validate(tag)

    async def update_tag(self, tag_id: int, tag_vo: AdminTagUpdateVO) -> AdminTagDTO:
        """
        更新标签。

        :param tag_id: 标签 ID
        :param tag_vo: 标签更新参数
        :return: 标签详情
        :raises MyException: 标签不存在时抛出
        """
        tag = await self.admin_tag_dao.get_tag_by_id(tag_id)
        if not tag:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = tag_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        if data.get("parent_id") == tag_id:
            raise MyException(ErrorCode.PARAM_ERROR)
        tag = await self.admin_tag_dao.update_tag(tag, data)
        return AdminTagDTO.model_validate(tag)

    async def delete_tag(self, tag_id: int) -> None:
        """
        删除标签。

        :param tag_id: 标签 ID
        :return: None
        :raises MyException: 标签不存在或存在子级时抛出
        """
        tag = await self.admin_tag_dao.get_tag_by_id(tag_id)
        if not tag:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        if await self.admin_tag_dao.has_tag_children(tag_id):
            raise MyException(ErrorCode.MENU_HAS_SUB_ITEM)
        await self.admin_tag_dao.delete_tag(tag_id)

    def _build_tag_tree(self, tags: list[Tag]) -> list[AdminTagDTO]:
        """
        构建标签树。

        :param tags: 标签列表
        :return: 标签树
        """
        node_map = {tag.id: AdminTagDTO.model_validate(tag) for tag in tags}
        for node in node_map.values():
            node.children = []
        roots = []
        for tag in tags:
            node = node_map[tag.id]
            parent = node_map.get(tag.parent_id)
            if parent:
                parent.children.append(node)
            else:
                roots.append(node)
        return roots
