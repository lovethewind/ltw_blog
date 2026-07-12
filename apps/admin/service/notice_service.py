from apps.admin.dao.notice_dao import AdminNoticeDao
from apps.admin.dto.notice_dto import AdminNoticeDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.notice_vo import AdminNoticeQueryVO, AdminNoticeUpdateVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException


@Component()
class AdminNoticeService(AdminBaseService):
    """后台通知服务。"""

    admin_notice_dao: AdminNoticeDao = Autowired()

    async def list_notices(self, query_vo: AdminNoticeQueryVO) -> dict:
        """
        分页查询通知。

        :param query_vo: 通知查询参数
        :return: 通知分页数据
        """
        notices, total = await self.admin_notice_dao.list_notices(
            query_vo.current, query_vo.size, query_vo.keyword, query_vo.user_id, query_vo.notice_type, query_vo.is_read
        )
        records = [AdminNoticeDTO.model_validate(notice) for notice in notices]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_notice(self, notice_id: int) -> AdminNoticeDTO:
        """
        查询通知详情。

        :param notice_id: 通知 ID
        :return: 通知详情
        :raises MyException: 通知不存在时抛出
        """
        notice = await self.admin_notice_dao.get_notice_by_id(notice_id)
        if not notice:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminNoticeDTO.model_validate(notice)

    async def update_notice(self, notice_id: int, notice_vo: AdminNoticeUpdateVO) -> AdminNoticeDTO:
        """
        更新通知。

        :param notice_id: 通知 ID
        :param notice_vo: 通知更新参数
        :return: 通知详情
        :raises MyException: 通知不存在时抛出
        """
        notice = await self.admin_notice_dao.get_notice_by_id(notice_id)
        if not notice:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        notice = await self.admin_notice_dao.update_notice(notice, notice_vo.model_dump(exclude_none=True))
        return AdminNoticeDTO.model_validate(notice)

    async def delete_notice(self, notice_id: int) -> None:
        """
        删除通知。

        :param notice_id: 通知 ID
        :return: None
        :raises MyException: 通知不存在时抛出
        """
        notice = await self.admin_notice_dao.get_notice_by_id(notice_id)
        if not notice:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_notice_dao.delete_notice(notice_id)
