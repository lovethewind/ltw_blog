from datetime import datetime

from apps.admin.dto.base_dto import BaseDTO


class AdminWebsiteDTO(BaseDTO):
    """
    后台网站导航 DTO。
    """

    id: int
    user_id: int
    name: str
    category_id: int
    cover: str
    introduce: str
    url: str
    index: int
    status: int
    create_time: datetime
    update_time: datetime
