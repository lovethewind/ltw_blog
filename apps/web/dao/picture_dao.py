# @Time    : 2024/10/22 14:51
# @Author  : frank
# @File    : picture_dao.py
from apps.base.core.depend_inject import Component
from apps.base.models.picture import Picture


@Component()
class PictureDao:

    async def get_picture(self, picture_id: int):
        return await Picture.filter(id=picture_id).first()
