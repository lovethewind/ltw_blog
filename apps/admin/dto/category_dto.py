from apps.admin.dto.base_dto import BaseDTO


class AdminCategoryDTO(BaseDTO):
    """
    后台分类 DTO。
    """

    id: int
    name: str
    description: str | None = None
    index: int
    is_active: bool
