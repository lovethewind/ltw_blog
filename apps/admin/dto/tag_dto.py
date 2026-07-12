from pydantic import Field

from apps.admin.dto.base_dto import BaseDTO


class AdminTagDTO(BaseDTO):
    """
    后台标签 DTO。
    """

    id: int
    parent_id: int
    name: str
    description: str | None = None
    level: int
    index: int
    is_active: bool
    children: list["AdminTagDTO"] = Field(default_factory=list)
