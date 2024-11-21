# @Time    : 2024/8/23 14:35
# @Author  : frank
# @File    : category_controller.py
from fastapi import APIRouter

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.category_service import CategoryService

router = APIRouter(prefix="/category", tags=["分类模块"])


@Controller(router)
class CategoryController:
    categoryService: CategoryService = Autowired()

    @router.get("/common/findAll", summary="查询出所有分类")
    async def find_all(self):
        """
        查询出所有分类
        :return:
        """
        ret = await self.categoryService.find_all()
        return ResponseUtil.success(ret)
