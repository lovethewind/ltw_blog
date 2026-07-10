import math

from apps.admin.core.context_vars import AdminContextVars
from apps.admin.dao.user_dao import AdminUserDao
from apps.admin.dto.user_dto import AdminUserDTO, AdminUserInfoDTO
from apps.admin.service.menu_service import AdminMenuService
from apps.admin.vo.user_vo import AdminUserCreateVO, AdminUserQueryVO, AdminUserRoleUpdateVO, AdminUserUpdateVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.user import User
from apps.base.utils.encrypt_util import EncryptUtil
from apps.base.utils.redis_util import RedisUtil


@Component()
class AdminUserService:
    """
    后台用户服务。
    """

    admin_user_dao: AdminUserDao = Autowired()
    admin_menu_service: AdminMenuService = Autowired()
    redis_util: RedisUtil = Autowired()

    async def info(self) -> AdminUserInfoDTO:
        """
        获取当前后台管理员信息。

        :return: 当前管理员信息
        :raises MyException: 管理员不存在时抛出
        """
        user_id = AdminContextVars.token_user_id.get()
        if not user_id:
            raise MyException(ErrorCode.ACCOUNT_NOT_EXIST)
        user = await self.admin_user_dao.get_admin_user_by_id(user_id)
        if not user:
            raise MyException(ErrorCode.ACCOUNT_NOT_EXIST)
        user_info = AdminUserInfoDTO.model_validate(user)
        user_info.home_path = "/analytics"
        user_info.real_name = user_info.nickname or user_info.username
        user_info.roles = ["super", "admin"]
        user_info.permissions = ["admin"]
        return user_info

    async def menus(self) -> list[dict]:
        """
        获取当前后台管理员菜单。

        :return: 菜单列表
        :raises MyException: 管理员不存在时抛出
        """
        user_id = AdminContextVars.token_user_id.get()
        if not user_id:
            raise MyException(ErrorCode.ACCOUNT_NOT_EXIST)
        user = await self.admin_user_dao.get_admin_user_by_id(user_id)
        if not user:
            raise MyException(ErrorCode.ACCOUNT_NOT_EXIST)
        return await self.admin_menu_service.get_current_route_menus(user)

    async def list_users(self, query_vo: AdminUserQueryVO) -> dict:
        """
        分页查询后台用户。

        :param query_vo: 用户查询参数
        :return: 用户分页数据
        """
        users, total = await self.admin_user_dao.list_users(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
        )
        role_map = await self.admin_user_dao.list_user_role_ids([user.id for user in users])
        records = [self._dump_user(user, role_map.get(user.id, [])) for user in users]
        return {
            "current": query_vo.current,
            "pages": math.ceil(total / query_vo.size) if query_vo.size else 0,
            "records": records,
            "size": query_vo.size,
            "total": total,
        }

    async def get_user(self, user_id: int) -> AdminUserDTO:
        """
        查询后台用户详情。

        :param user_id: 用户 ID
        :return: 用户详情
        :raises MyException: 用户不存在时抛出
        """
        user = await self.admin_user_dao.get_user_by_id(user_id)
        if not user:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        role_ids = await self.admin_user_dao.get_user_role_ids(user_id)
        return self._dump_user(user, role_ids)

    async def create_user(self, user_vo: AdminUserCreateVO) -> AdminUserDTO:
        """
        创建后台用户。

        :param user_vo: 用户创建参数
        :return: 用户详情
        :raises MyException: 账号、邮箱或手机号已存在时抛出
        """
        data = user_vo.model_dump(exclude={"role_ids"}, exclude_none=True)
        self._normalize_user_data(data)
        await self._check_unique_fields(data)
        data["password"] = EncryptUtil.encrypt(data["password"])
        data["uid"] = self.redis_util.User.gen_uid()
        user = await self.admin_user_dao.create_user(data, user_vo.role_ids)
        return self._dump_user(user, user_vo.role_ids)

    async def update_user(self, user_id: int, user_vo: AdminUserUpdateVO) -> AdminUserDTO:
        """
        更新后台用户。

        :param user_id: 用户 ID
        :param user_vo: 用户更新参数
        :return: 用户详情
        :raises MyException: 用户不存在或唯一字段冲突时抛出
        """
        user = await self.admin_user_dao.get_user_by_id(user_id)
        if not user:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = user_vo.model_dump(exclude={"role_ids"}, exclude_none=True)
        self._normalize_user_data(data)
        await self._check_unique_fields(data, exclude_user_id=user_id)
        if data.get("password"):
            data["password"] = EncryptUtil.encrypt(data["password"])
        role_ids = user_vo.role_ids
        user = await self.admin_user_dao.update_user(user, data, role_ids)
        if role_ids is None:
            role_ids = await self.admin_user_dao.get_user_role_ids(user_id)
        return self._dump_user(user, role_ids)

    async def delete_user(self, user_id: int) -> None:
        """
        删除后台用户。

        :param user_id: 用户 ID
        :return: None
        :raises MyException: 用户不存在或删除当前账号时抛出
        """
        current_user_id = AdminContextVars.token_user_id.get()
        if current_user_id == user_id:
            raise MyException(ErrorCode.ACCOUNT_CANT_DELETE_SELF)
        user = await self.admin_user_dao.get_user_by_id(user_id)
        if not user:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_user_dao.delete_user(user_id)

    async def get_user_role_ids(self, user_id: int) -> list[int]:
        """
        查询用户角色授权。

        :param user_id: 用户 ID
        :return: 角色 ID 列表
        :raises MyException: 用户不存在时抛出
        """
        user = await self.admin_user_dao.get_user_by_id(user_id)
        if not user:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return await self.admin_user_dao.get_user_role_ids(user_id)

    async def update_user_roles(self, user_id: int, user_role_vo: AdminUserRoleUpdateVO) -> None:
        """
        更新用户角色授权。

        :param user_id: 用户 ID
        :param user_role_vo: 用户角色授权参数
        :return: None
        :raises MyException: 用户不存在时抛出
        """
        user = await self.admin_user_dao.get_user_by_id(user_id)
        if not user:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_user_dao.update_user_roles(user_id, user_role_vo.role_ids)

    async def _check_unique_fields(self, data: dict, exclude_user_id: int | None = None) -> None:
        """
        校验用户唯一字段。

        :param data: 用户数据
        :param exclude_user_id: 排除的用户 ID
        :return: None
        :raises MyException: 唯一字段已存在时抛出
        """
        for field in ("username", "email", "mobile", "wechat"):
            value = data.get(field)
            if value and await self.admin_user_dao.exists_user_field(field, value, exclude_user_id):
                raise MyException(ErrorCode.ACCOUNT_HAS_EXIST)

    def _normalize_user_data(self, data: dict) -> None:
        """
        规范化用户保存数据。

        :param data: 用户数据
        :return: None
        """
        for field in ("email", "mobile", "wechat"):
            if data.get(field) == "":
                data[field] = None
        for field in ("avatar", "last_login_ip", "summary", "background", "address"):
            if data.get(field) is None:
                data[field] = ""

    def _dump_user(self, user: User, role_ids: list[int]) -> AdminUserDTO:
        """
        转换后台用户响应数据。

        :param user: 用户对象
        :param role_ids: 角色 ID 列表
        :return: 用户响应数据
        """
        dto = AdminUserDTO.model_validate(user)
        dto.role_ids = role_ids
        return dto
