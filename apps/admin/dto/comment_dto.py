from datetime import datetime

from apps.admin.dto.base_dto import BaseDTO


class AdminCommentUserDTO(BaseDTO):
    """后台评论用户摘要 DTO。"""

    id: int
    uid: int
    username: str
    nickname: str
    avatar: str | None = None


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
    user: AdminCommentUserDTO | None = None
    obj_content: str | None = None
    parent_content: str | None = None
