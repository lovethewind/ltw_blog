from datetime import datetime

from apps.admin.dto.base_dto import BaseDTO


class AdminMessageDTO(BaseDTO):
    """
    后台留言 DTO。
    """

    id: int
    user_id: int
    avatar: str | None = None
    nickname: str | None = None
    email: str | None = None
    address: str
    content: str
    parent_id: int
    reply_user_id: int
    first_level_id: int
    create_time: datetime
    update_time: datetime
