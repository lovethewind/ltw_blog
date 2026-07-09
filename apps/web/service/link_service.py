from sqlalchemy import select

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.common import CheckStatusEnum
from apps.base.models.link import Link
from apps.web.dto.link_dto import LinkDTO
from apps.web.vo.link_vo import LinkVO


@Component()
class LinkService:

    async def list_links(self) -> list[LinkDTO]:
        """
        获取已通过审核的友链列表。

        :return: 友链 DTO 列表。
        """
        stmt = select(Link).where(Link.status == CheckStatusEnum.PASS.value)
        links = await db.model_all(stmt)
        return LinkDTO.bulk_model_validate(links)

    async def add(self, link_vo: LinkVO) -> None:
        """
        添加待审核友链。

        :param link_vo: 友链提交参数。
        :return: None。
        """
        link = Link(**link_vo.model_dump())
        link.status = CheckStatusEnum.CHECKING.value
        await db.create(link, return_value=False)
