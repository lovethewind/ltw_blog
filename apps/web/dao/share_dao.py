# @Time    : 2024/10/22 14:54
# @Author  : frank
# @File    : share_dao.py
from apps.base.core.depend_inject import Component
from apps.base.models.share import Share


@Component()
class ShareDao:

    async def get_share(self, share_id: int):
        return await Share.filter(id=share_id).first()
