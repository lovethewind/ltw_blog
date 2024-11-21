# @Time    : 2024/9/2 15:03
# @Author  : frank
# @File    : link_dto.py
from apps.web.dto.base_dto import BaseDTO


class LinkDTO(BaseDTO):
    id: int
    name: str
    cover: str
    introduce: str
    url: str
