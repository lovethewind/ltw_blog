# @Time    : 2024/9/2 14:57
# @Author  : frank
# @File    : link_service.py
from apps.base.core.depend_inject import Component
from apps.base.enum.common import CheckStatusEnum
from apps.base.models.link import Link
from apps.web.dto.link_dto import LinkDTO
from apps.web.vo.link_vo import LinkVO


@Component()
class LinkService:

    async def list_links(self):
        """
        获取友链列表
        :return:
        """
        links = await Link.filter(status=CheckStatusEnum.PASS)
        ret = LinkDTO.bulk_model_validate(links)
        return ret

    async def add(self, link_vo: LinkVO):
        """
        添加友链
        :param link_vo:
        :return:
        """
        link = Link(**link_vo.model_dump())
        link.status = CheckStatusEnum.CHECKING
        await link.save()
