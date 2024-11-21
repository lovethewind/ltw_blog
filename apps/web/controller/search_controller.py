# @Time    : 2024/10/14 14:03
# @Author  : frank
# @File    : search_controller.py
from fastapi import APIRouter

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.search_service import SearchService
from apps.web.vo.search_vo import ArticleSearchVO, ArticleRecommendVO, UserSearchVO

router = APIRouter(prefix="/search", tags=["搜索模块"])


@Controller(router)
class SearchController:
    search_service: SearchService = Autowired()

    @router.post("/common/article/list", summary="ES根据关键词查找文章")
    async def get_es_article_list(self, search_vo: ArticleSearchVO):
        """
        ES根据关键词查找文章
        :param search_vo:
        :return:
        """
        ret = await self.search_service.get_es_article_list(search_vo)
        return ResponseUtil.success(ret)

    @router.post("/common/user/list", summary="搜索用户")
    async def get_user_list(self, search_vo: UserSearchVO):
        """
        搜索用户
        :param search_vo:
        :return:
        """
        ret = await self.search_service.get_user_list(search_vo)
        return ResponseUtil.success(ret)

    @router.get("/common/hotWords", summary="获取每日热搜前10个关键字")
    async def get_daily_hot_words_list(self):
        """
        获取每日热搜前10个关键字
        :return:
        """
        ret = await self.search_service.get_daily_hot_words_list()
        return ResponseUtil.success(ret)

    @router.post("/common/article/recommend", summary="获取相关文章的推荐文章")
    async def get_recommend_article_list(self, article_recommend_vo: ArticleRecommendVO):
        """
        获取相关文章的推荐文章
        :param article_recommend_vo:
        :return:
        """
        ret = await self.search_service.get_recommend_article_list(article_recommend_vo)
        return ResponseUtil.success(ret)

    @router.get("/common/init", summary="初始化article索引")
    async def init_article_index(self):
        """
        初始化article索引
        :return:
        """
        await self.search_service.init_article_index()
        return ResponseUtil.success()
