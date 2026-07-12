from datetime import datetime

from apps.admin.dto.base_dto import BaseDTO


class AdminSourceDTO(BaseDTO):
    """
    后台资源 DTO。
    """

    id: int
    user_id: int
    url: str
    is_deleted: bool
    create_time: datetime
    update_time: datetime
