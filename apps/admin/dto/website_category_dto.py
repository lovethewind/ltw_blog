from datetime import datetime

from apps.admin.dto.base_dto import BaseDTO


class AdminWebsiteCategoryDTO(BaseDTO):
    """
    后台网站导航分类 DTO。
    """

    id: int
    name: str
    index: int
    create_time: datetime
    update_time: datetime
