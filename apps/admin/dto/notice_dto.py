from datetime import datetime

from pydantic import Field

from apps.admin.dto.base_dto import BaseDTO


class AdminNoticeDTO(BaseDTO):
    """
    后台通知 DTO。
    """

    id: int
    user_id: int
    title: str
    content: str
    notice_type: int
    is_read: bool
    detail: dict = Field(default_factory=dict)
    create_time: datetime
    update_time: datetime
