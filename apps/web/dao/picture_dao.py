# @Time    : 2024/10/22 14:51
# @Author  : frank
# @File    : picture_dao.py
from sqlalchemy import select

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.picture import Picture


@Component()
class PictureDao:

    async def get_picture(self, picture_id: int) -> Picture | None:
        """
        根据图片 ID 获取图片。

        :param picture_id: 图片 ID。
        :return: 图片对象；不存在时返回 None。
        """
        return await db.model_first(select(Picture).where(Picture.id == picture_id))
