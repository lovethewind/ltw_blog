# @Time    : 2024/9/12 14:40
# @Author  : frank
# @File    : action_controller.py
from fastapi import APIRouter, Depends, Body

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.action_service import ActionService
from apps.web.vo.action_vo import ActionQueryVO, ActionAddVO, ActionTypeDetailQueryVO

router = APIRouter(prefix="/action", tags=["行为模块"])


@Controller(router)
class ActionController:
    action_service: ActionService = Autowired()

    @router.post("/common/list/{current}/{size}", summary="获取行为列表")
    async def list_actions(self, current: int, size: int, action_query_vo: ActionQueryVO = Depends(),
                           action_type_detail_query_vo: ActionTypeDetailQueryVO = Body()):
        """
        获取行为列表
        :param current:
        :param size:
        :param action_query_vo:
        :param action_type_detail_query_vo:
        :return:
        """
        ret = await self.action_service.list_actions(current, size, action_query_vo, action_type_detail_query_vo)
        return ResponseUtil.success(ret)

    @router.post("/list/{current}/{size}", summary="获取用户行为列表")
    async def list_user_actions(self, current: int, size: int, action_query_vo: ActionQueryVO = Depends(),
                                action_type_detail_query_vo: ActionTypeDetailQueryVO = Body()):
        """
        获取用户行为列表
        :param current:
        :param size:
        :param action_query_vo:
        :param action_type_detail_query_vo:
        :return:
        """
        ret = await self.action_service.list_user_actions(current, size, action_query_vo, action_type_detail_query_vo)
        return ResponseUtil.success(ret)

    @router.post("/addOrUpdate", summary="添加行为")
    async def add_or_update(self, action_add_vo: ActionAddVO):
        """
        添加行为
        :param action_add_vo:
        :return:
        """
        ret = await self.action_service.add_or_update(action_add_vo)
        return ResponseUtil.success(ret)
