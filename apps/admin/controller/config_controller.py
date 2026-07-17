from fastapi import Body, Depends
from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.service.config_service import AdminConfigService
from apps.admin.service.search_analysis_service import AdminSearchAnalysisService
from apps.admin.utils.depends_util import permission
from apps.admin.vo.config_vo import AdminConfigCreateVO, AdminConfigQueryVO, AdminConfigUpdateVO
from apps.admin.vo.search_analysis_vo import SearchAnalysisConfigVO, SearchAnalysisPreviewVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/config", tags=["后台配置管理"])


@Controller(router)
class AdminConfigController:
    """后台配置控制器。"""

    admin_config_service: AdminConfigService = Autowired()
    search_analysis_service: AdminSearchAnalysisService = Autowired()

    @router.get("/search-analysis", summary="查询搜索分词配置")
    @permission("config:query")
    async def get_search_analysis(self) -> Response:
        """查询搜索分词配置。"""
        return ResponseUtil.success(await self.search_analysis_service.get_state())

    @router.put("/search-analysis/draft", summary="保存搜索分词草稿")
    @permission("config:update")
    async def save_search_analysis_draft(self, config_vo: SearchAnalysisConfigVO = Body()) -> Response:
        """
        保存搜索分词草稿。

        :param config_vo: 搜索分词草稿。
        :return: 更新后的配置状态。
        """
        return ResponseUtil.success(await self.search_analysis_service.save_draft(config_vo))

    @router.post("/search-analysis/preview", summary="预览搜索分词")
    @permission("config:query")
    async def preview_search_analysis(self, preview_vo: SearchAnalysisPreviewVO = Body()) -> Response:
        """
        预览搜索分词。

        :param preview_vo: 预览参数。
        :return: 分词结果。
        """
        return ResponseUtil.success(await self.search_analysis_service.preview(preview_vo))

    @router.post("/search-analysis/publish", summary="发布搜索分词配置")
    @permission("config:update")
    async def publish_search_analysis(self) -> Response:
        """发布当前搜索分词草稿。"""
        return ResponseUtil.success(await self.search_analysis_service.publish())

    @router.post("/search-analysis/rebuild-index", summary="重建文章搜索索引")
    @permission("config:update")
    async def rebuild_article_search_index(self) -> Response:
        """重建文章搜索索引并切换读写别名。"""
        return ResponseUtil.success(await self.search_analysis_service.rebuild_article_index())

    @router.get("/list", summary="分页查询配置")
    @permission("config:query")
    async def list_configs(self, query_vo: AdminConfigQueryVO = Depends()) -> Response:
        """
        分页查询配置。

        :param query_vo: 配置查询参数
        :return: 配置分页数据
        """
        ret = await self.admin_config_service.list_configs(query_vo)
        return ResponseUtil.success(ret)

    @router.get("/{config_id}", summary="查询配置详情")
    @permission("config:query")
    async def get_config(self, config_id: int) -> Response:
        """
        查询配置详情。

        :param config_id: 配置 ID
        :return: 配置详情
        """
        ret = await self.admin_config_service.get_config(config_id)
        return ResponseUtil.success(ret)

    @router.post("/create", summary="创建配置")
    @permission("config:create")
    async def create_config(self, config_vo: AdminConfigCreateVO = Body()) -> Response:
        """
        创建配置。

        :param config_vo: 配置创建参数
        :return: 配置详情
        """
        ret = await self.admin_config_service.create_config(config_vo)
        return ResponseUtil.success(ret)

    @router.put("/{config_id}", summary="更新配置")
    @permission("config:update")
    async def update_config(self, config_id: int, config_vo: AdminConfigUpdateVO = Body()) -> Response:
        """
        更新配置。

        :param config_id: 配置 ID
        :param config_vo: 配置更新参数
        :return: 配置详情
        """
        ret = await self.admin_config_service.update_config(config_id, config_vo)
        return ResponseUtil.success(ret)

    @router.delete("/{config_id}", summary="删除配置")
    @permission("config:delete")
    async def delete_config(self, config_id: int) -> Response:
        """
        删除配置。

        :param config_id: 配置 ID
        :return: 删除结果
        """
        await self.admin_config_service.delete_config(config_id)
        return ResponseUtil.success()
