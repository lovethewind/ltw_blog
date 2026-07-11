import datetime

from sqlalchemy import update

from apps.admin.dao.user_dao import AdminUserDao
from apps.admin.service.menu_service import AdminMenuService
from apps.admin.utils.token_util import AdminTokenUtil
from apps.admin.vo.auth_vo import AdminLoginVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.user import User
from apps.base.utils.encrypt_util import EncryptUtil


@Component()
class AdminAuthService:
    """
    后台认证服务。
    """

    admin_user_dao: AdminUserDao = Autowired()
    admin_menu_service: AdminMenuService = Autowired()

    async def login(self, login_vo: AdminLoginVO) -> dict[str, str]:
        """
        后台管理员登录。

        :param login_vo: 后台登录参数
        :return: 登录令牌
        :raises MyException: 账号不存在、密码错误或权限不足时抛出
        """
        user = await self.admin_user_dao.get_admin_user_by_username(login_vo.username)
        if not user:
            raise MyException(ErrorCode.ACCOUNT_NOT_EXIST)
        if not EncryptUtil.equals(login_vo.password, user.password):
            raise MyException(ErrorCode.PASSWORD_ERROR)
        user.last_login_time = datetime.datetime.now()
        await db.execute(update(User).where(User.id == user.id).values(last_login_time=user.last_login_time))
        token = AdminTokenUtil.create_token(user.id, user.username)
        return {
            "token": token,
            "accessToken": token,
        }

    async def codes(self) -> list[str]:
        """
        获取后台管理员权限码。

        :return: 权限码列表
        """
        return await self.admin_menu_service.get_current_button_codes()
