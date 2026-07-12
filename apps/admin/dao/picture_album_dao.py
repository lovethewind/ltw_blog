from typing import Any

from sqlalchemy import or_, select

from apps.admin.dao.base_dao import _create, _delete, _paginate, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.picture import PictureAlbum


@Component()
class AdminPictureAlbumDao:
    """后台相册数据访问对象。"""

    async def list_picture_albums(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        status: int | None = None,
        album_type: int | None = None,
        user_id: int | None = None,
    ) -> tuple[list[PictureAlbum], int]:
        """
        分页查询图册。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 图册关键词。
        :param status: 审核状态。
        :param album_type: 图册类型。
        :param user_id: 用户 ID。
        :return: 图册列表和总数。
        """
        stmt = select(PictureAlbum)
        if keyword:
            stmt = stmt.where(
                or_(PictureAlbum.name.ilike(f"%{keyword}%"), PictureAlbum.description.ilike(f"%{keyword}%"))
            )
        if status is not None:
            stmt = stmt.where(PictureAlbum.status == status)
        if album_type is not None:
            stmt = stmt.where(PictureAlbum.album_type == album_type)
        if user_id:
            stmt = stmt.where(PictureAlbum.user_id == user_id)
        return await _paginate(stmt, current, size, PictureAlbum.id.desc())

    async def get_picture_album_by_id(self, album_id: int) -> PictureAlbum | None:
        """
        根据 ID 查询图册。

        :param album_id: 图册 ID。
        :return: 图册对象。
        """
        return await db.model_first(select(PictureAlbum).where(PictureAlbum.id == album_id))

    async def create_picture_album(self, data: dict[str, Any]) -> PictureAlbum:
        """
        创建图册。

        :param data: 图册数据。
        :return: 图册对象。
        """
        return await _create(PictureAlbum, data)

    async def update_picture_album(self, album: PictureAlbum, data: dict[str, Any]) -> PictureAlbum:
        """
        更新图册。

        :param album: 图册对象。
        :param data: 更新数据。
        :return: 图册对象。
        """
        return await _update(album, data)

    async def delete_picture_album(self, album_id: int) -> None:
        """
        删除图册。

        :param album_id: 图册 ID。
        :return: None。
        """
        await _delete(PictureAlbum, album_id)
