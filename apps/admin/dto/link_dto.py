from datetime import datetime

from apps.admin.dto.base_dto import BaseDTO


class AdminLinkDTO(BaseDTO):
    """
    后台友链 DTO。
    """

    id: int
    name: str
    cover: str
    introduce: str
    url: str
    email: str | None = None
    index: int
    status: int
    description: str | None = None
    create_time: datetime
    update_time: datetime
