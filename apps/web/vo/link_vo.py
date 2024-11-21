# @Time    : 2024/9/2 15:05
# @Author  : frank
# @File    : link_vo.py
from apps.web.vo.base_vo import BaseVO


class LinkVO(BaseVO):
    name: str
    cover: str
    url: str
    introduce: str
    email: str
