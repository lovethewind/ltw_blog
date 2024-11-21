from fastapi import APIRouter, Depends

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.decorator_util import avoid_repeat_submit
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.article_service import ArticleService
from apps.web.vo.article_vo import ArticleQueryVO, ArticleVO, ArticleUpdateVO, ArticleAddViewCountVO
from apps.web.vo.batch_vo import BatchVO

router = APIRouter(prefix="/article", tags=["文章信息"])


@Controller(router)
class ArticleController:
    article_service: ArticleService = Autowired()

    @router.get("/common/list/{current}/{size}", summary="分页查询获取文章列表")
    async def list_articles(self, current: int, size: int, article_query_vo: ArticleQueryVO = Depends()):
        """
        分页查询获取文章列表
        :param current:
        :param size:
        :param article_query_vo:
        :return:
        """
        ret = await self.article_service.list_articles(current, size, article_query_vo)
        return ResponseUtil.success(ret)

    @router.post("/add", summary="添加文章")
    @avoid_repeat_submit("添加文章重复提交")
    async def add(self, article_vo: ArticleVO):
        ret = await self.article_service.add(article_vo)
        return ResponseUtil.success(ret)

    @router.get("/common/find/{article_id}", summary="根据文章id获取文章信息")
    async def detail(self, article_id: int):
        ret = await self.article_service.detail(article_id)
        return ResponseUtil.success(ret)

    @router.post("/common/addViewCount", summary="增加文章浏览量")
    @avoid_repeat_submit("文章浏览量防重复提交", timeout=60, not_err=True, complete_release=False)
    async def add_view_count(self, article_add_view_count_vo: ArticleAddViewCountVO):
        await self.article_service.add_view_count(article_add_view_count_vo)
        return ResponseUtil.success()

    @router.get("/editFind/{article_id}", summary="编辑页面根据文章id获取文章信息")
    async def edit_find(self, article_id: int):
        """
        编辑页面根据文章id获取文章信息
        :param article_id:
        :return:
        """
        ret = await self.article_service.edit_find(article_id)
        return ResponseUtil.success(ret)

    @router.put("/update", summary="更新文章信息")
    async def update(self, article_update_vo: ArticleUpdateVO):
        """
        更新文章信息
        :param article_update_vo:
        :return:
        """
        ret = await self.article_service.update(article_update_vo)
        return ResponseUtil.success(ret)

    @router.get("/articleCountInfo", summary="获取文章数量信息")
    async def article_count_info(self, article_query_vo: ArticleQueryVO = Depends()):
        """
        获取文章数量信息
        :param article_query_vo:
        :return:
        """
        ret = await self.article_service.article_count_info(article_query_vo)
        return ResponseUtil.success(ret)

    @router.delete("/removeToRecycle", summary="移动文章至回收站")
    async def remove_to_recycle(self, batch_vo: BatchVO):
        """
        移动文章至回收站
        :param batch_vo:
        :return:
        """
        await self.article_service.remove_to_recycle(batch_vo)
        return ResponseUtil.success()

    @router.delete("/removeFromRecycle", summary="删除回收站的文章")
    async def remove_from_recycle(self, batch_vo: BatchVO):
        """
        删除回收站的文章
        :param batch_vo:
        :return:
        """
        await self.article_service.remove_from_recycle(batch_vo)
        return ResponseUtil.success()

    @router.put("/moveToDraft", summary="将回收站的文章恢复至草稿箱")
    async def move_to_draft(self, batch_vo: BatchVO):
        """
        将回收站的文章恢复至草稿箱
        :param batch_vo:
        :return:
        """
        await self.article_service.move_to_draft(batch_vo)
        return ResponseUtil.success()
