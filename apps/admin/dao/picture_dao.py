from typing import Any

from sqlalchemy import select

from apps.admin.dao.base_dao import _create, _delete, _paginate, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.picture import Picture


@Component()
class AdminPictureDao:
    """后台图片数据访问对象。"""

    async def list_pictures(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        album_id: int | None = None,
        status: int | None = None,
        user_id: int | None = None,
    ) -> tuple[list[Picture], int]:
        """
        分页查询图片。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 图片说明关键词。
        :param album_id: 图册 ID。
        :param status: 审核状态。
        :param user_id: 用户 ID。
        :return: 图片列表和总数。
        """
        stmt = select(Picture)
        if keyword:
            stmt = stmt.where(Picture.description.ilike(f"%{keyword}%"))
        if album_id:
            stmt = stmt.where(Picture.album_id == album_id)
        if status is not None:
            stmt = stmt.where(Picture.status == status)
        if user_id:
            stmt = stmt.where(Picture.user_id == user_id)
        return await _paginate(stmt, current, size, Picture.id.desc())

    async def get_picture_by_id(self, picture_id: int) -> Picture | None:
        """
        根据 ID 查询图片。

        :param picture_id: 图片 ID。
        :return: 图片对象。
        """
        return await db.model_first(select(Picture).where(Picture.id == picture_id))

    async def create_picture(self, data: dict[str, Any]) -> Picture:
        """
        创建图片。

        :param data: 图片数据。
        :return: 图片对象。
        """
        return await _create(Picture, data)

    async def update_picture(self, picture: Picture, data: dict[str, Any]) -> Picture:
        """
        更新图片。

        :param picture: 图片对象。
        :param data: 更新数据。
        :return: 图片对象。
        """
        return await _update(picture, data)

    async def delete_picture(self, picture_id: int) -> None:
        """
        删除图片。

        :param picture_id: 图片 ID。
        :return: None。
        """
        await _delete(Picture, picture_id)
