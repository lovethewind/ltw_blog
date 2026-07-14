from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.analytics_service import AdminAnalyticsService
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/analytics", tags=["后台运营分析"])


@Controller(router)
class AdminAnalyticsController:
    """后台运营分析控制器。"""

    admin_analytics_service: AdminAnalyticsService = Autowired()

    @router.get("/overview", summary="查询运营分析数据")
    async def get_analytics(self) -> Response:
        """
        查询后台运营分析数据。

        :return: 运营分析数据。
        """
        ret = await self.admin_analytics_service.get_analytics()
        return ResponseUtil.success(ret)
