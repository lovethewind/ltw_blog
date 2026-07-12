from datetime import datetime

from apps.admin.dto.base_dto import BaseDTO


class AdminUserRestrictionDTO(BaseDTO):
    """
    后台用户限制 DTO。
    """

    id: int
    user_id: int
    restrict_type: int
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_forever: bool
    reason: str | None = None
    is_cancel: bool
    cancel_time: datetime | None = None
    cancel_reason: str | None = None
    create_time: datetime
    update_time: datetime
