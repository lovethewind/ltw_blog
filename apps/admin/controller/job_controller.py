from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.job_service import AdminJobService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.job_vo import AdminJobCreateVO, AdminJobQueryVO, AdminJobStatusVO, AdminJobUpdateVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/job", tags=["后台定时任务管理"])


@Controller(router)
class AdminJobController:
    """后台定时任务控制器。"""

    admin_job_service: AdminJobService = Autowired()

    @router.get("/list", summary="分页查询定时任务")
    @permission("job:query")
    async def list_jobs(self, query_vo: AdminJobQueryVO = Depends()) -> Response:
        """
        分页查询定时任务。

        :param query_vo: 定时任务查询参数
        :return: 定时任务分页数据
        """
        ret = await self.admin_job_service.list_jobs(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/{job_id}", summary="查询定时任务详情")
    @permission("job:query")
    async def get_job(self, job_id: int) -> Response:
        """
        查询定时任务详情。

        :param job_id: 定时任务 ID
        :return: 定时任务详情
        """
        ret = await self.admin_job_service.get_job(job_id)
        return ResponseUtil.success(ret)

    @router.post("/create", summary="创建定时任务")
    @permission("job:create")
    async def create_job(self, job_vo: AdminJobCreateVO = Body()) -> Response:
        """
        创建定时任务。

        :param job_vo: 定时任务创建参数
        :return: 定时任务详情
        """
        ret = await self.admin_job_service.create_job(job_vo)
        return ResponseUtil.success(ret)

    @router.put("/{job_id}", summary="更新定时任务")
    @permission("job:update")
    async def update_job(self, job_id: int, job_vo: AdminJobUpdateVO = Body()) -> Response:
        """
        更新定时任务。

        :param job_id: 定时任务 ID
        :param job_vo: 定时任务更新参数
        :return: 定时任务详情
        """
        ret = await self.admin_job_service.update_job(job_id, job_vo)
        return ResponseUtil.success(ret)

    @router.put("/{job_id}/status", summary="更新定时任务状态")
    @permission("job:status")
    async def update_job_status(self, job_id: int, status_vo: AdminJobStatusVO = Body()) -> Response:
        """
        更新定时任务状态。

        :param job_id: 定时任务 ID
        :param status_vo: 状态更新参数
        :return: 定时任务详情
        """
        ret = await self.admin_job_service.update_job_status(job_id, status_vo)
        return ResponseUtil.success(ret)

    @router.delete("/{job_id}", summary="删除定时任务")
    @permission("job:delete")
    async def delete_job(self, job_id: int) -> Response:
        """
        删除定时任务。

        :param job_id: 定时任务 ID
        :return: 删除结果
        """
        await self.admin_job_service.delete_job(job_id)
        return ResponseUtil.success()
