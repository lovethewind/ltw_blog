from datetime import datetime

from apps.admin.dto.base_dto import BaseDTO


class AdminPictureDTO(BaseDTO):
    """
    后台图片 DTO。
    """

    id: int
    user_id: int
    album_id: int
    description: str | None = None
    url: str
    thumb_url: str = ""
    size: int
    width: int
    height: int
    status: int
    create_time: datetime
    update_time: datetime
