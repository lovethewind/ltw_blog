import math
from collections.abc import Sequence
from datetime import datetime

from apps.admin.dao.operation_dao import AdminOperationDao
from apps.admin.dto.base_dto import BaseDTO
from apps.admin.dto.operation_dto import AdminJobDTO, AdminNoticeDTO, AdminSourceDTO, AdminUserRestrictionDTO
from apps.admin.vo.operation_vo import (
    AdminJobCreateVO,
    AdminJobQueryVO,
    AdminJobStatusVO,
    AdminJobUpdateVO,
    AdminNoticeQueryVO,
    AdminNoticeUpdateVO,
    AdminSourceQueryVO,
    AdminSourceUpdateVO,
    AdminUserRestrictionCancelVO,
    AdminUserRestrictionCreateVO,
    AdminUserRestrictionQueryVO,
    AdminUserRestrictionUpdateVO,
)
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException


@Component()
class AdminOperationService:
    """
    后台运营管理服务。
    """

    admin_operation_dao: AdminOperationDao = Autowired()

    async def list_jobs(self, query_vo: AdminJobQueryVO) -> dict:
        """
        分页查询定时任务。

        :param query_vo: 定时任务查询参数
        :return: 定时任务分页数据
        """
        jobs, total = await self.admin_operation_dao.list_jobs(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.group,
            query_vo.status,
        )
        records = [AdminJobDTO.model_validate(job) for job in jobs]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_job(self, job_id: int) -> AdminJobDTO:
        """
        查询定时任务详情。

        :param job_id: 定时任务 ID
        :return: 定时任务详情
        :raises MyException: 定时任务不存在时抛出
        """
        job = await self.admin_operation_dao.get_job_by_id(job_id)
        if not job:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminJobDTO.model_validate(job)

    async def create_job(self, job_vo: AdminJobCreateVO) -> AdminJobDTO:
        """
        创建定时任务。

        :param job_vo: 定时任务创建参数
        :return: 定时任务详情
        """
        data = job_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        job = await self.admin_operation_dao.create_job(data)
        return AdminJobDTO.model_validate(job)

    async def update_job(self, job_id: int, job_vo: AdminJobUpdateVO) -> AdminJobDTO:
        """
        更新定时任务。

        :param job_id: 定时任务 ID
        :param job_vo: 定时任务更新参数
        :return: 定时任务详情
        :raises MyException: 定时任务不存在时抛出
        """
        job = await self.admin_operation_dao.get_job_by_id(job_id)
        if not job:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = job_vo.model_dump(exclude_none=True)
        self._normalize_description(data)
        job = await self.admin_operation_dao.update_job(job, data)
        return AdminJobDTO.model_validate(job)

    async def update_job_status(self, job_id: int, status_vo: AdminJobStatusVO) -> AdminJobDTO:
        """
        更新定时任务状态。

        :param job_id: 定时任务 ID
        :param status_vo: 状态更新参数
        :return: 定时任务详情
        :raises MyException: 定时任务不存在时抛出
        """
        job = await self.admin_operation_dao.get_job_by_id(job_id)
        if not job:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = status_vo.model_dump(exclude_none=True)
        job = await self.admin_operation_dao.update_job(job, data)
        return AdminJobDTO.model_validate(job)

    async def delete_job(self, job_id: int) -> None:
        """
        删除定时任务。

        :param job_id: 定时任务 ID
        :return: None
        :raises MyException: 定时任务不存在时抛出
        """
        job = await self.admin_operation_dao.get_job_by_id(job_id)
        if not job:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_operation_dao.delete_job(job_id)

    async def list_sources(self, query_vo: AdminSourceQueryVO) -> dict:
        """
        分页查询资源。

        :param query_vo: 资源查询参数
        :return: 资源分页数据
        """
        sources, total = await self.admin_operation_dao.list_sources(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.user_id,
            query_vo.is_deleted,
        )
        records = [AdminSourceDTO.model_validate(source) for source in sources]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def update_source(self, source_id: int, source_vo: AdminSourceUpdateVO) -> AdminSourceDTO:
        """
        更新资源。

        :param source_id: 资源 ID
        :param source_vo: 资源更新参数
        :return: 资源详情
        :raises MyException: 资源不存在时抛出
        """
        source = await self.admin_operation_dao.get_source_by_id(source_id)
        if not source:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        source = await self.admin_operation_dao.update_source(source, source_vo.model_dump(exclude_none=True))
        return AdminSourceDTO.model_validate(source)

    async def delete_source(self, source_id: int) -> None:
        """
        删除资源。

        :param source_id: 资源 ID
        :return: None
        :raises MyException: 资源不存在时抛出
        """
        source = await self.admin_operation_dao.get_source_by_id(source_id)
        if not source:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_operation_dao.delete_source(source_id)

    async def list_notices(self, query_vo: AdminNoticeQueryVO) -> dict:
        """
        分页查询通知。

        :param query_vo: 通知查询参数
        :return: 通知分页数据
        """
        notices, total = await self.admin_operation_dao.list_notices(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.user_id,
            query_vo.notice_type,
            query_vo.is_read,
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
        notice = await self.admin_operation_dao.get_notice_by_id(notice_id)
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
        notice = await self.admin_operation_dao.get_notice_by_id(notice_id)
        if not notice:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        notice = await self.admin_operation_dao.update_notice(notice, notice_vo.model_dump(exclude_none=True))
        return AdminNoticeDTO.model_validate(notice)

    async def delete_notice(self, notice_id: int) -> None:
        """
        删除通知。

        :param notice_id: 通知 ID
        :return: None
        :raises MyException: 通知不存在时抛出
        """
        notice = await self.admin_operation_dao.get_notice_by_id(notice_id)
        if not notice:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_operation_dao.delete_notice(notice_id)

    async def list_user_restrictions(self, query_vo: AdminUserRestrictionQueryVO) -> dict:
        """
        分页查询用户限制。

        :param query_vo: 用户限制查询参数
        :return: 用户限制分页数据
        """
        restrictions, total = await self.admin_operation_dao.list_user_restrictions(
            query_vo.current,
            query_vo.size,
            query_vo.user_id,
            query_vo.restrict_type,
            query_vo.is_cancel,
        )
        records = [AdminUserRestrictionDTO.model_validate(restriction) for restriction in restrictions]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def create_user_restriction(self, restriction_vo: AdminUserRestrictionCreateVO) -> AdminUserRestrictionDTO:
        """
        创建用户限制。

        :param restriction_vo: 用户限制创建参数
        :return: 用户限制详情
        """
        data = restriction_vo.model_dump(exclude_none=True)
        self._normalize_restriction_data(data)
        restriction = await self.admin_operation_dao.create_user_restriction(data)
        return AdminUserRestrictionDTO.model_validate(restriction)

    async def update_user_restriction(
        self,
        restriction_id: int,
        restriction_vo: AdminUserRestrictionUpdateVO,
    ) -> AdminUserRestrictionDTO:
        """
        更新用户限制。

        :param restriction_id: 用户限制 ID
        :param restriction_vo: 用户限制更新参数
        :return: 用户限制详情
        :raises MyException: 用户限制不存在时抛出
        """
        restriction = await self.admin_operation_dao.get_user_restriction_by_id(restriction_id)
        if not restriction:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = restriction_vo.model_dump(exclude_none=True)
        self._normalize_restriction_data(data)
        restriction = await self.admin_operation_dao.update_user_restriction(restriction, data)
        return AdminUserRestrictionDTO.model_validate(restriction)

    async def cancel_user_restriction(
        self,
        restriction_id: int,
        cancel_vo: AdminUserRestrictionCancelVO,
    ) -> AdminUserRestrictionDTO:
        """
        解除用户限制。

        :param restriction_id: 用户限制 ID
        :param cancel_vo: 解除参数
        :return: 用户限制详情
        :raises MyException: 用户限制不存在时抛出
        """
        restriction = await self.admin_operation_dao.get_user_restriction_by_id(restriction_id)
        if not restriction:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = {
            "is_cancel": True,
            "cancel_time": datetime.now(),
            "cancel_reason": cancel_vo.cancel_reason or "",
        }
        restriction = await self.admin_operation_dao.update_user_restriction(restriction, data)
        return AdminUserRestrictionDTO.model_validate(restriction)

    async def delete_user_restriction(self, restriction_id: int) -> None:
        """
        删除用户限制。

        :param restriction_id: 用户限制 ID
        :return: None
        :raises MyException: 用户限制不存在时抛出
        """
        restriction = await self.admin_operation_dao.get_user_restriction_by_id(restriction_id)
        if not restriction:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_operation_dao.delete_user_restriction(restriction_id)

    def _normalize_description(self, data: dict[str, object]) -> None:
        """
        规范化描述字段。

        :param data: 保存数据
        :return: None
        """
        if "description" in data and data["description"] is None:
            data["description"] = ""

    def _normalize_restriction_data(self, data: dict[str, object]) -> None:
        """
        规范化用户限制保存数据。

        :param data: 用户限制数据
        :return: None
        """
        for field in ("reason", "cancel_reason"):
            if field in data and data[field] is None:
                data[field] = ""

    def _page_result(self, current: int, size: int, total: int, records: Sequence[BaseDTO]) -> dict:
        """
        构建分页响应。

        :param current: 当前页码
        :param size: 每页条数
        :param total: 总数
        :param records: 数据列表
        :return: 分页响应
        """
        return {
            "current": current,
            "pages": math.ceil(total / size) if size else 0,
            "records": records,
            "size": size,
            "total": total,
        }
