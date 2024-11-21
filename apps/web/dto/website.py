# @Time    : 2024/9/1 23:37
# @Author  : frank
# @File    : website.py
from typing import Optional

from apps.web.dto.base_dto import BaseDTO


class WebsiteDTO(BaseDTO):
    id: int
    name: str
    cover: str
    introduce: str
    url: str


class WebsiteCategoryDTO(BaseDTO):
    id: int
    name: str
    website_list: Optional[list[WebsiteDTO]] = []
