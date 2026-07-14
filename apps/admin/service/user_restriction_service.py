from datetime import datetime

from apps.admin.dao.user_restriction_dao import AdminUserRestrictionDao
from apps.admin.dto.user_restriction_dto import AdminUserRestrictionDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.utils.redis_util import AdminRedisUtil
from apps.admin.vo.user_restriction_vo import (
    AdminUserRestrictionCancelVO,
    AdminUserRestrictionCreateVO,
    AdminUserRestrictionQueryVO,
    AdminUserRestrictionUpdateVO,
)
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException


@Component()
class AdminUserRestrictionService(AdminBaseService):
    """后台用户限制服务。"""

    admin_user_restriction_dao: AdminUserRestrictionDao = Autowired()
    redis_util: AdminRedisUtil = Autowired()

    async def list_user_restrictions(self, query_vo: AdminUserRestrictionQueryVO) -> dict:
        """
        分页查询用户限制。

        :param query_vo: 用户限制查询参数
        :return: 用户限制分页数据
        """
        restrictions, total = await self.admin_user_restriction_dao.list_user_restrictions(
            query_vo.current, query_vo.size, query_vo.user_id, query_vo.restrict_type, query_vo.is_cancel
        )
        records = AdminUserRestrictionDTO.bulk_model_validate(restrictions)
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def create_user_restriction(self, restriction_vo: AdminUserRestrictionCreateVO) -> AdminUserRestrictionDTO:
        """
        创建用户限制。

        :param restriction_vo: 用户限制创建参数
        :return: 用户限制详情
        """
        data = restriction_vo.model_dump(exclude_none=True)
        self._normalize_restriction_data(data)
        restriction = await self.admin_user_restriction_dao.create_user_restriction(data)
        await self.redis_util.User.delete_user_profile_cache(restriction.user_id)
        return AdminUserRestrictionDTO.model_validate(restriction)

    async def update_user_restriction(
        self, restriction_id: int, restriction_vo: AdminUserRestrictionUpdateVO
    ) -> AdminUserRestrictionDTO:
        """
        更新用户限制。

        :param restriction_id: 用户限制 ID
        :param restriction_vo: 用户限制更新参数
        :return: 用户限制详情
        :raises MyException: 用户限制不存在时抛出
        """
        restriction = await self.admin_user_restriction_dao.get_user_restriction_by_id(restriction_id)
        if not restriction:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = restriction_vo.model_dump(exclude_none=True)
        self._normalize_restriction_data(data)
        restriction = await self.admin_user_restriction_dao.update_user_restriction(restriction, data)
        await self.redis_util.User.delete_user_profile_cache(restriction.user_id)
        return AdminUserRestrictionDTO.model_validate(restriction)

    async def cancel_user_restriction(
        self, restriction_id: int, cancel_vo: AdminUserRestrictionCancelVO
    ) -> AdminUserRestrictionDTO:
        """
        解除用户限制。

        :param restriction_id: 用户限制 ID
        :param cancel_vo: 解除参数
        :return: 用户限制详情
        :raises MyException: 用户限制不存在时抛出
        """
        restriction = await self.admin_user_restriction_dao.get_user_restriction_by_id(restriction_id)
        if not restriction:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = {"is_cancel": True, "cancel_time": datetime.now(), "cancel_reason": cancel_vo.cancel_reason or ""}
        restriction = await self.admin_user_restriction_dao.update_user_restriction(restriction, data)
        await self.redis_util.User.delete_user_profile_cache(restriction.user_id)
        return AdminUserRestrictionDTO.model_validate(restriction)

    async def delete_user_restriction(self, restriction_id: int) -> None:
        """
        删除用户限制。

        :param restriction_id: 用户限制 ID
        :return: None
        :raises MyException: 用户限制不存在时抛出
        """
        restriction = await self.admin_user_restriction_dao.get_user_restriction_by_id(restriction_id)
        if not restriction:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_user_restriction_dao.delete_user_restriction(restriction_id)
        await self.redis_util.User.delete_user_profile_cache(restriction.user_id)

    def _normalize_restriction_data(self, data: dict[str, object]) -> None:
        """
        规范化用户限制保存数据。

        :param data: 用户限制数据
        :return: None
        """
        for field in ("reason", "cancel_reason"):
            if field in data and data[field] is None:
                data[field] = ""
