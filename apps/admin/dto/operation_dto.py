from datetime import datetime

from pydantic import Field

from apps.admin.dto.base_dto import BaseDTO


class AdminJobDTO(BaseDTO):
    """
    后台定时任务 DTO。
    """

    id: int
    name: str
    group: str
    invoke_target: str
    cron_expression: str
    misfire_policy: int
    concurrent: bool
    status: int
    create_user_id: int
    update_user_id: int | None = None
    description: str | None = None
    create_time: datetime
    update_time: datetime


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
