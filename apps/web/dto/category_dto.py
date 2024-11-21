# @Time    : 2024/8/23 14:40
# @Author  : frank
# @File    : category_dto.py
from typing import Optional

from apps.web.dto.base_dto import BaseDTO


class CategoryDTO(BaseDTO):
    id: int
    name: str
    description: str
    index: int
    article_count: Optional[int] = 0


class TagDTO(BaseDTO):
    id: int
    name: str
    description: str
    parent_id: int
    index: int
    children: Optional[list["TagDTO"]] = []