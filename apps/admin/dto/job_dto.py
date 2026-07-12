from datetime import datetime

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
