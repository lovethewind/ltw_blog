# @Time    : 2024/9/1 22:50
# @Author  : frank
# @File    : website_service.py
from apps.base.core.depend_inject import Component
from apps.base.enum.website import WebsiteStatusEnum
from apps.base.models.website import WebsiteCategory, Website
from apps.web.core.context_vars import ContextVars
from apps.web.dto.website import WebsiteCategoryDTO, WebsiteDTO
from apps.web.vo.website_vo import WebsiteVO


@Component()
class WebsiteService:

    async def list_websites(self):
        """
        获取网站导航列表
        :return:
        """
        websites = await Website.filter(status=WebsiteStatusEnum.PASS).order_by("index")
        category_list = await WebsiteCategory.filter().order_by("index")
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

    async def add(self, website_vo: WebsiteVO):
        """
        添加网站导航
        :param website_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        website = Website(**website_vo.model_dump())
        website.user_id = user_id
        website.status = WebsiteStatusEnum.CHECK
        await website.save()
