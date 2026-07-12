from apps.admin.dao.picture_album_dao import AdminPictureAlbumDao
from apps.admin.dto.picture_album_dto import AdminPictureAlbumDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.picture_album_vo import (
    AdminPictureAlbumCreateVO,
    AdminPictureAlbumQueryVO,
    AdminPictureAlbumUpdateVO,
)
from apps.admin.vo.status_vo import AdminCheckStatusVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException


@Component()
class AdminPictureAlbumService(AdminBaseService):
    """后台相册服务。"""

    admin_picture_album_dao: AdminPictureAlbumDao = Autowired()

    async def list_picture_albums(self, query_vo: AdminPictureAlbumQueryVO) -> dict:
        """
        分页查询图册。

        :param query_vo: 图册查询参数
        :return: 图册分页数据
        """
        albums, total = await self.admin_picture_album_dao.list_picture_albums(
            query_vo.current, query_vo.size, query_vo.keyword, query_vo.status, query_vo.album_type, query_vo.user_id
        )
        records = [AdminPictureAlbumDTO.model_validate(album) for album in albums]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_picture_album(self, album_id: int) -> AdminPictureAlbumDTO:
        """
        查询图册详情。

        :param album_id: 图册 ID
        :return: 图册详情
        :raises MyException: 图册不存在时抛出
        """
        album = await self.admin_picture_album_dao.get_picture_album_by_id(album_id)
        if not album:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminPictureAlbumDTO.model_validate(album)

    async def create_picture_album(self, album_vo: AdminPictureAlbumCreateVO) -> AdminPictureAlbumDTO:
        """
        创建图册。

        :param album_vo: 图册创建参数
        :return: 图册详情
        """
        data = album_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        album = await self.admin_picture_album_dao.create_picture_album(data)
        return AdminPictureAlbumDTO.model_validate(album)

    async def update_picture_album(self, album_id: int, album_vo: AdminPictureAlbumUpdateVO) -> AdminPictureAlbumDTO:
        """
        更新图册。

        :param album_id: 图册 ID
        :param album_vo: 图册更新参数
        :return: 图册详情
        :raises MyException: 图册不存在时抛出
        """
        album = await self.admin_picture_album_dao.get_picture_album_by_id(album_id)
        if not album:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = album_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        album = await self.admin_picture_album_dao.update_picture_album(album, data)
        return AdminPictureAlbumDTO.model_validate(album)

    async def update_picture_album_status(self, album_id: int, status_vo: AdminCheckStatusVO) -> AdminPictureAlbumDTO:
        """
        更新图册审核状态。

        :param album_id: 图册 ID
        :param status_vo: 审核状态参数
        :return: 图册详情
        :raises MyException: 图册不存在时抛出
        """
        album = await self.admin_picture_album_dao.get_picture_album_by_id(album_id)
        if not album:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        album = await self.admin_picture_album_dao.update_picture_album(album, {"status": status_vo.status})
        return AdminPictureAlbumDTO.model_validate(album)

    async def delete_picture_album(self, album_id: int) -> None:
        """
        删除图册。

        :param album_id: 图册 ID
        :return: None
        :raises MyException: 图册不存在时抛出
        """
        album = await self.admin_picture_album_dao.get_picture_album_by_id(album_id)
        if not album:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_picture_album_dao.delete_picture_album(album_id)
