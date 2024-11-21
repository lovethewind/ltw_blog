# @Time    : 2024/9/1 23:45
# @Author  : frank
# @File    : website_vo.py
from apps.web.vo.base_vo import BaseVO


class WebsiteVO(BaseVO):
    name: str
    category_id: int
    url: str
    cover: str
    introduce: str