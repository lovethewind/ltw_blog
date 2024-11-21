from fastapi import Body
from fastapi.routing import APIRouter

from apps.base.enum.user import WechatCodeTypeEnum
from apps.base.utils.decorator_util import avoid_repeat_submit
from apps.base.utils.response_util import ResponseUtil
from apps.base.core.depend_inject import Autowired, Controller
from apps.web.dto.user_dto import UserSettingsType
from apps.web.service.user_service import UserService
from apps.web.vo.user_vo import LoginVO, RegisterVO, ChangePasswordVO, UserUpdateVO, WechatBindParamsVO, \
    ForgetPasswordVO, ChangeEmailBindVO, ChangeMobileBindVO, AddUserViewCountVO

router = APIRouter(prefix="/user", tags=["用户信息"])


@Controller(router)
class UserController:
    user_service: UserService = Autowired()

    @router.post("/common/login", summary="登录")
    async def login(self, login_vo: LoginVO = Body()):
        """
        用户登录
        :param login_vo:
        :return:
        """
        ret = await self.user_service.login(login_vo)
        return ResponseUtil.success(ret)

    @router.get("/info", summary="根据token获取信息")
    async def info(self):
        """
        根据token获取信息
        :return:
        """
        ret = await self.user_service.info()
        return ResponseUtil.success(ret)

    @router.get("/common/unblock/{key}", summary="解除登录限制")
    async def unblock(self, key: str):
        """
        根据token获取信息
        :return:
        """
        await self.user_service.unblock(key)
        return ResponseUtil.success()

    @router.post("/common/emailRegister", summary="邮箱注册")
    @avoid_repeat_submit("邮箱注册重复提交", renew=True)
    async def email_register(self, register_vo: RegisterVO):
        """
        邮箱注册
        :param register_vo:
        :return:
        """
        ret = await self.user_service.email_register(register_vo)
        return ResponseUtil.success(ret)

    @router.post("/common/mobileRegister", summary="手机号注册")
    @avoid_repeat_submit("手机号注册重复提交", renew=True)
    async def mobile_register(self, register_vo: RegisterVO):
        """
        手机号注册
        :param register_vo:
        :return:
        """
        ret = await self.user_service.mobile_register(register_vo)
        return ResponseUtil.success(ret)

    @router.get("/common/find/{user_id}", summary="获取某一用户信息")
    async def get_user_info(self, user_id: int):
        """
        获取某一用户信息
        :param user_id:
        :return:
        """
        ret = await self.user_service.get_user_info(user_id)
        return ResponseUtil.success(ret)

    @router.get("/common/findByUid/{uid}", summary="获取某一用户信息(通过uid)")
    async def get_user_info_by_uid(self, uid: int):
        """
        获取某一用户信息
        :param uid:
        :return:
        """
        ret = await self.user_service.get_user_info(uid, by_uid=True)
        return ResponseUtil.success(ret)

    @router.post("/common/addViewCount", summary="增加用户浏览量")
    @avoid_repeat_submit("用户访问量防重复提交", timeout=60, not_err=True, complete_release=False)
    async def add_view_count(self, add_user_view_count_vo: AddUserViewCountVO):
        """
        增加用户访问量
        :param add_user_view_count_vo:
        :return:
        """
        await self.user_service.add_view_count(add_user_view_count_vo)
        return ResponseUtil.success()

    @router.put("/common/changePasswordByFind", summary="利用忘记密码更改密码")
    async def change_password_by_find(self, forget_password_vo: ForgetPasswordVO):
        """
        利用忘记忘记密码更改密码
        :param forget_password_vo:
        :return:
        """
        await self.user_service.change_password_by_find(forget_password_vo)
        return ResponseUtil.success()

    @router.put("/changePasswordByLogin", summary="登录后更改密码")
    async def change_password_by_login(self, change_password_vo: ChangePasswordVO):
        """
        登录后更改密码
        :param change_password_vo:
        :return:
        """
        await self.user_service.change_password_by_login(change_password_vo)
        return ResponseUtil.success()

    @router.put("/update", summary="更新用户信息")
    async def update(self, user_update_vo: UserUpdateVO):
        """
        更新用户信息
        :param user_update_vo:
        :return:
        """
        await self.user_service.update_user_info(user_update_vo)
        return ResponseUtil.success()

    @router.post("/saveUserSettings", summary="保存用户设置")
    async def save_user_settings(self, user_settings: UserSettingsType):
        """
        保存用户设置
        :param user_settings:
        :return:
        """
        await self.user_service.save_user_settings(user_settings)
        return ResponseUtil.success()

    @router.put("/changeEmailBind", summary="修改邮箱绑定")
    @avoid_repeat_submit("修改邮箱绑定重复提交", renew=True)
    async def change_email_bind(self, change_email_bind_vo: ChangeEmailBindVO):
        """
        修改邮箱绑定
        :param change_email_bind_vo:
        :return:
        """
        await self.user_service.change_email_bind(change_email_bind_vo)
        return ResponseUtil.success()

    @router.put("/changeMobileBind", summary="修改手机号绑定")
    @avoid_repeat_submit("修改手机号绑定重复提交", renew=True)
    async def change_mobile_bind(self, change_mobile_bind_vo: ChangeMobileBindVO):
        """
        修改手机号绑定
        :param change_mobile_bind_vo:
        :return:
        """
        await self.user_service.change_mobile_bind(change_mobile_bind_vo)
        return ResponseUtil.success()

    ##################################### 微信相关接口 ###############################

    @router.post("/common/wechatRegister", summary="微信注册")
    @avoid_repeat_submit("微信注册重复提交", renew=True)
    async def wechat_register(self, register_vo: RegisterVO):
        """
        微信注册
        :param register_vo:
        :return:
        """
        ret = await self.user_service.wechat_register(register_vo)
        return ResponseUtil.success(ret)

    @router.get("/common/wechat/getWechatAppletCode/{code_type}", summary="获取微信小程序码")
    async def get_wechat_applet_code(self, code_type: WechatCodeTypeEnum):
        """
        获取微信小程序码
        :param code_type:
        :return:
        """
        ret = await self.user_service.get_wechat_applet_code(code_type)
        return ResponseUtil.success(ret)

    @router.post("/common/wechat/checkScan", summary="验证是否已经扫码")
    async def check_scan(self, code: str = Body(embed=True)):
        """
        验证是否已经扫码
        :param code:
        :return:
        """
        ret = await self.user_service.check_scan(code)
        return ResponseUtil.success(ret)

    @router.post("/wechat/checkOldScan", summary="换绑微信验证旧微信")
    async def check_old_scan(self, code: str = Body(embed=True)):
        """
        换绑微信验证旧微信
        :param code:
        :return:
        """
        ret = await self.user_service.check_old_scan(code)
        return ResponseUtil.success(ret)

    @router.post("/wechat/checkChangePasswordScan", summary="修改密码验证微信")
    async def check_change_password_scan(self, code: str = Body(embed=True)):
        """
        修改密码验证微信
        :param code:
        :return:
        """
        ret = await self.user_service.check_change_password_scan(code)
        return ResponseUtil.success(ret)

    @router.post("/common/wechat/scanCallback", summary="微信扫码成功获取用户信息")
    async def scan_callback(self, code: str = Body(embed=True), state: str = Body(embed=True)):
        """
        微信扫码成功获取用户信息
        :param code: 服务器随机生成的code
        :param state: 登录凭证code
        :return:
        """
        ret = await self.user_service.scan_callback(code, state)
        return ResponseUtil.success(ret)

    @router.post("/wechat/bind", summary="绑定微信")
    async def bind_wechat(self, wechat_bind_params_vo: WechatBindParamsVO):
        """
        绑定微信
        :param wechat_bind_params_vo:
        :return:
        """
        await self.user_service.bind_wechat(wechat_bind_params_vo)
        return ResponseUtil.success()

    @router.post("/common/wechat/userInfo", summary="小程序获取用户信息")
    async def get_wechat_user_info(self, code: str = Body(embed=True)):
        """
        小程序获取用户信息
        :param code: 微信登录获取的code
        :return:
        """
        ret = await self.user_service.get_wechat_user_info(code)
        return ResponseUtil.success(ret)
