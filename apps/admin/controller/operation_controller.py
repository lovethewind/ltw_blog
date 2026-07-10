from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.operation_service import AdminOperationService
from apps.admin.utils.depends_util import permission
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
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/operation", tags=["后台运营管理"])


@Controller(router)
class AdminOperationController:
    """
    后台运营管理控制器。
    """

    admin_operation_service: AdminOperationService = Autowired()

    @router.get("/job/list", summary="分页查询定时任务")
    @permission("operation:job:query")
    async def list_jobs(self, query_vo: AdminJobQueryVO = Depends()) -> Response:
        """
        分页查询定时任务。

        :param query_vo: 定时任务查询参数
        :return: 定时任务分页数据
        """
        ret = await self.admin_operation_service.list_jobs(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/job/{job_id}", summary="查询定时任务详情")
    @permission("operation:job:query")
    async def get_job(self, job_id: int) -> Response:
        """
        查询定时任务详情。

        :param job_id: 定时任务 ID
        :return: 定时任务详情
        """
        ret = await self.admin_operation_service.get_job(job_id)
        return ResponseUtil.success(ret)

    @router.post("/job", summary="创建定时任务")
    @permission("operation:job:create")
    async def create_job(self, job_vo: AdminJobCreateVO = Body()) -> Response:
        """
        创建定时任务。

        :param job_vo: 定时任务创建参数
        :return: 定时任务详情
        """
        ret = await self.admin_operation_service.create_job(job_vo)
        return ResponseUtil.success(ret)

    @router.put("/job/{job_id}", summary="更新定时任务")
    @permission("operation:job:update")
    async def update_job(self, job_id: int, job_vo: AdminJobUpdateVO = Body()) -> Response:
        """
        更新定时任务。

        :param job_id: 定时任务 ID
        :param job_vo: 定时任务更新参数
        :return: 定时任务详情
        """
        ret = await self.admin_operation_service.update_job(job_id, job_vo)
        return ResponseUtil.success(ret)

    @router.put("/job/{job_id}/status", summary="更新定时任务状态")
    @permission("operation:job:status")
    async def update_job_status(self, job_id: int, status_vo: AdminJobStatusVO = Body()) -> Response:
        """
        更新定时任务状态。

        :param job_id: 定时任务 ID
        :param status_vo: 状态更新参数
        :return: 定时任务详情
        """
        ret = await self.admin_operation_service.update_job_status(job_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/job/{job_id}", summary="删除定时任务")
    @permission("operation:job:delete")
    async def delete_job(self, job_id: int) -> Response:
        """
        删除定时任务。

        :param job_id: 定时任务 ID
        :return: 删除结果
        """
        await self.admin_operation_service.delete_job(job_id)
        return ResponseUtil.success()

    @router.get("/source/list", summary="分页查询资源")
    @permission("operation:source:query")
    async def list_sources(self, query_vo: AdminSourceQueryVO = Depends()) -> Response:
        """
        分页查询资源。

        :param query_vo: 资源查询参数
        :return: 资源分页数据
        """
        ret = await self.admin_operation_service.list_sources(query_vo)
        return ResponseUtil.success(ret)

    @router.put("/source/{source_id}", summary="更新资源")
    @permission("operation:source:update")
    async def update_source(self, source_id: int, source_vo: AdminSourceUpdateVO = Body()) -> Response:
        """
        更新资源。

        :param source_id: 资源 ID
        :param source_vo: 资源更新参数
        :return: 资源详情
        """
        ret = await self.admin_operation_service.update_source(source_id, source_vo)
        return ResponseUtil.success(ret)

    @router.delete("/source/{source_id}", summary="删除资源")
    @permission("operation:source:delete")
    async def delete_source(self, source_id: int) -> Response:
        """
        删除资源。

        :param source_id: 资源 ID
        :return: 删除结果
        """
        await self.admin_operation_service.delete_source(source_id)
        return ResponseUtil.success()

    @router.get("/notice/list", summary="分页查询通知")
    @permission("operation:notice:query")
    async def list_notices(self, query_vo: AdminNoticeQueryVO = Depends()) -> Response:
        """
        分页查询通知。

        :param query_vo: 通知查询参数
        :return: 通知分页数据
        """
        ret = await self.admin_operation_service.list_notices(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/notice/{notice_id}", summary="查询通知详情")
    @permission("operation:notice:query")
    async def get_notice(self, notice_id: int) -> Response:
        """
        查询通知详情。

        :param notice_id: 通知 ID
        :return: 通知详情
        """
        ret = await self.admin_operation_service.get_notice(notice_id)
        return ResponseUtil.success(ret)

    @router.put("/notice/{notice_id}", summary="更新通知")
    @permission("operation:notice:update")
    async def update_notice(self, notice_id: int, notice_vo: AdminNoticeUpdateVO = Body()) -> Response:
        """
        更新通知。

        :param notice_id: 通知 ID
        :param notice_vo: 通知更新参数
        :return: 通知详情
        """
        ret = await self.admin_operation_service.update_notice(notice_id, notice_vo)
        return ResponseUtil.success(ret)

    @router.delete("/notice/{notice_id}", summary="删除通知")
    @permission("operation:notice:delete")
    async def delete_notice(self, notice_id: int) -> Response:
        """
        删除通知。

        :param notice_id: 通知 ID
        :return: 删除结果
        """
        await self.admin_operation_service.delete_notice(notice_id)
        return ResponseUtil.success()

    @router.get("/restriction/list", summary="分页查询用户限制")
    @permission("operation:restriction:query")
    async def list_user_restrictions(self, query_vo: AdminUserRestrictionQueryVO = Depends()) -> Response:
        """
        分页查询用户限制。

        :param query_vo: 用户限制查询参数
        :return: 用户限制分页数据
        """
        ret = await self.admin_operation_service.list_user_restrictions(query_vo)
        return ResponseUtil.success(ret)

    @router.post("/restriction", summary="创建用户限制")
    @permission("operation:restriction:create")
    async def create_user_restriction(self, restriction_vo: AdminUserRestrictionCreateVO = Body()) -> Response:
        """
        创建用户限制。

        :param restriction_vo: 用户限制创建参数
        :return: 用户限制详情
        """
        ret = await self.admin_operation_service.create_user_restriction(restriction_vo)
        return ResponseUtil.success(ret)

    @router.put("/restriction/{restriction_id}", summary="更新用户限制")
    @permission("operation:restriction:update")
    async def update_user_restriction(
        self,
        restriction_id: int,
        restriction_vo: AdminUserRestrictionUpdateVO = Body(),
    ) -> Response:
        """
        更新用户限制。

        :param restriction_id: 用户限制 ID
        :param restriction_vo: 用户限制更新参数
        :return: 用户限制详情
        """
        ret = await self.admin_operation_service.update_user_restriction(restriction_id, restriction_vo)
        return ResponseUtil.success(ret)

    @router.put("/restriction/{restriction_id}/cancel", summary="解除用户限制")
    @permission("operation:restriction:cancel")
    async def cancel_user_restriction(
        self,
        restriction_id: int,
        cancel_vo: AdminUserRestrictionCancelVO = Body(),
    ) -> Response:
        """
        解除用户限制。

        :param restriction_id: 用户限制 ID
        :param cancel_vo: 解除参数
        :return: 用户限制详情
        """
        ret = await self.admin_operation_service.cancel_user_restriction(restriction_id, cancel_vo)
        return ResponseUtil.success(ret)

    @router.delete("/restriction/{restriction_id}", summary="删除用户限制")
    @permission("operation:restriction:delete")
    async def delete_user_restriction(self, restriction_id: int) -> Response:
        """
        删除用户限制。

        :param restriction_id: 用户限制 ID
        :return: 删除结果
        """
        await self.admin_operation_service.delete_user_restriction(restriction_id)
        return ResponseUtil.success()
