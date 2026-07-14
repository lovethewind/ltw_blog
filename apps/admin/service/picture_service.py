from apps.admin.dao.picture_dao import AdminPictureDao
from apps.admin.dto.picture_dto import AdminPictureDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.picture_vo import AdminPictureCreateVO, AdminPictureQueryVO, AdminPictureUpdateVO
from apps.admin.vo.status_vo import AdminCheckStatusVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException


@Component()
class AdminPictureService(AdminBaseService):
    """后台图片服务。"""

    admin_picture_dao: AdminPictureDao = Autowired()

    async def list_pictures(self, query_vo: AdminPictureQueryVO) -> dict:
        """
        分页查询图片。

        :param query_vo: 图片查询参数
        :return: 图片分页数据
        """
        pictures, total = await self.admin_picture_dao.list_pictures(
            query_vo.current, query_vo.size, query_vo.keyword, query_vo.album_id, query_vo.status, query_vo.user_id
        )
        records = AdminPictureDTO.bulk_model_validate(pictures)
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_picture(self, picture_id: int) -> AdminPictureDTO:
        """
        查询图片详情。

        :param picture_id: 图片 ID
        :return: 图片详情
        :raises MyException: 图片不存在时抛出
        """
        picture = await self.admin_picture_dao.get_picture_by_id(picture_id)
        if not picture:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminPictureDTO.model_validate(picture)

    async def create_picture(self, picture_vo: AdminPictureCreateVO) -> AdminPictureDTO:
        """
        创建图片。

        :param picture_vo: 图片创建参数
        :return: 图片详情
        """
        data = picture_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        self._fill_thumbnail_url(data, "url", "thumb_url")
        picture = await self.admin_picture_dao.create_picture(data)
        return AdminPictureDTO.model_validate(picture)

    async def update_picture(self, picture_id: int, picture_vo: AdminPictureUpdateVO) -> AdminPictureDTO:
        """
        更新图片。

        :param picture_id: 图片 ID
        :param picture_vo: 图片更新参数
        :return: 图片详情
        :raises MyException: 图片不存在时抛出
        """
        picture = await self.admin_picture_dao.get_picture_by_id(picture_id)
        if not picture:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = picture_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        self._fill_thumbnail_url(data, "url", "thumb_url")
        picture = await self.admin_picture_dao.update_picture(picture, data)
        return AdminPictureDTO.model_validate(picture)

    async def update_picture_status(self, picture_id: int, status_vo: AdminCheckStatusVO) -> AdminPictureDTO:
        """
        更新图片审核状态。

        :param picture_id: 图片 ID
        :param status_vo: 审核状态参数
        :return: 图片详情
        :raises MyException: 图片不存在时抛出
        """
        picture = await self.admin_picture_dao.get_picture_by_id(picture_id)
        if not picture:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        picture = await self.admin_picture_dao.update_picture(picture, {"status": status_vo.status})
        return AdminPictureDTO.model_validate(picture)

    async def delete_picture(self, picture_id: int) -> None:
        """
        删除图片。

        :param picture_id: 图片 ID
        :return: None
        :raises MyException: 图片不存在时抛出
        """
        picture = await self.admin_picture_dao.get_picture_by_id(picture_id)
        if not picture:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_picture_dao.delete_picture(picture_id)
