from datetime import datetime

from apps.admin.dto.base_dto import BaseDTO


class AdminPictureAlbumDTO(BaseDTO):
    """
    后台图册 DTO。
    """

    id: int
    user_id: int
    name: str
    description: str | None = None
    cover: str
    status: int
    album_type: int
    create_time: datetime
    update_time: datetime
