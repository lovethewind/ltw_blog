from datetime import datetime

from apps.admin.dto.base_dto import BaseDTO


class AdminCommentDTO(BaseDTO):
    """
    后台评论 DTO。
    """

    id: int
    user_id: int
    obj_id: int
    obj_type: int
    parent_id: int
    reply_user_id: int
    first_level_id: int
    content: str
    status: int
    create_time: datetime
    update_time: datetime
