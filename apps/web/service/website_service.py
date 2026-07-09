import asyncio

from sqlalchemy import select

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.website import WebsiteStatusEnum
from apps.base.models.website import Website, WebsiteCategory
from apps.web.core.context_vars import ContextVars
from apps.web.dto.website import WebsiteCategoryDTO, WebsiteDTO
from apps.web.vo.website_vo import WebsiteVO


@Component()
class WebsiteService:

    async def list_websites(self) -> list[WebsiteCategoryDTO]:
        """
        获取网站导航列表。

        :return: 网站导航分类 DTO 列表。
        """
        website_stmt = select(Website).where(Website.status == WebsiteStatusEnum.PASS.value).order_by(Website.index)
        category_stmt = select(WebsiteCategory).order_by(WebsiteCategory.index)
        websites, category_list = await asyncio.gather(
            db.model_all(website_stmt),
            db.model_all(category_stmt),
        )
        website_dict = {}
        for website in websites:
            if website.category_id not in website_dict:
                website_dict[website.category_id] = []
            website_dict[website.category_id].append(WebsiteDTO.model_validate(website, from_attributes=True))
        ret = []
        for category in category_list:
            dto = WebsiteCategoryDTO.model_validate(category, from_attributes=True)
            dto.website_list = website_dict.get(category.id, [])
            ret.append(dto)
        return ret

    async def add(self, website_vo: WebsiteVO) -> None:
        """
        添加待审核网站导航。

        :param website_vo: 网站导航提交参数。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        website = Website(**website_vo.model_dump())
        website.user_id = user_id
        website.status = WebsiteStatusEnum.CHECK.value
        await db.create(website, return_value=False)
