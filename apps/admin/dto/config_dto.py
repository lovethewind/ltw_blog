from datetime import datetime

from apps.admin.dto.base_dto import BaseDTO


class AdminConfigDTO(BaseDTO):
    """
    后台配置 DTO。
    """

    id: int
    name: str
    value: str
    description: str | None = None
    is_active: bool
    create_time: datetime
    update_time: datetime
