import asyncio
import datetime
from ipaddress import ip_address

import pytz
from starlette.requests import Request
from tortoise import transactions
from tortoise.expressions import Q

from apps.base.constant.email_constant import EmailConstant
from apps.base.enum.article import ArticleStatusEnum
from apps.base.enum.comment import CommentStatusEnum
from apps.base.enum.common import VerifyCodeTypeEnum
from apps.base.enum.error_code import ErrorCode
from apps.base.enum.notice import NoticeTypeEnum
from apps.base.enum.user import UserTagEnum, GenderEnum, UserRestrictionTypeEnum, WechatCodeTypeEnum
from apps.base.exception.my_exception import MyException
from apps.base.models.article import Article
from apps.base.models.comment import Comment
from apps.base.models.user import User, UserRestriction, UserSettings
from apps.base.utils.desensitized_util import DesensitizedUtil
from apps.base.utils.encrypt_util import EncryptUtil
from apps.base.utils.ip_util import IpUtil
from apps.base.utils.picture_util import PictureUtil
from apps.base.utils.random_util import RandomUtil
from apps.base.utils.redis_util import RedisUtil
from apps.base.core.depend_inject import Component, Autowired, logger, Value, RefreshScope
from apps.base.utils.wechat_util import WechatUtil
from apps.web.core.context_vars import ContextVars
from apps.web.core.event.event_name import EventName
from apps.web.core.event.event_server import EventServer
from apps.web.core.kafka.util import KafkaUtil
from apps.web.dao.chat_dao import ChatDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.chat_dto import WSMessageDTO
from apps.web.dto.notice_dto import NoticeSaveDTO

from apps.web.dto.user_dto import UserInfoDTO, UserCommonInfoDTO, UserRestrictionDTO, WechatScanResultDTO, \
    UserBaseInfoDTO, WechatScanResultEnum, UserSettingsType
from apps.web.utils.token_util import TokenUtil
from apps.web.utils.ws_util import manager
from apps.web.vo.user_vo import LoginVO, RegisterVO, ChangePasswordVO, ChangePasswordTypeEnum, UserUpdateVO, \
    WechatBindParamsVO, ForgetPasswordVO, ChangeEmailBindVO, ChangeMobileBindVO, AddUserViewCountVO


@Component()
@RefreshScope("app.web")
class UserService:
    user_dao: UserDao = Autowired()
    chat_dao: ChatDao = Autowired()
    redis_util: RedisUtil = Autowired()
    wechat_util: WechatUtil = Autowired()
    picture_util: PictureUtil = Autowired()
    kafka_util: KafkaUtil = Autowired()
    MAX_ERROR_TIMES: str = Value("app.web.max-error-login-times")
    UNBLOCK_LOGIN_URL: str = Value("app.web.unblock-login-url")
    event_server = EventServer.get_instance()

    async def login(self, login_vo: LoginVO):
        """
        多种方式登录
        """
        request = ContextVars.request.get()
        q = User.filter()
        if login_vo.username:
            q = q.filter(username=login_vo.username)
        elif login_vo.email:
            q = q.filter(email=login_vo.email)
        elif login_vo.mobile:
            q = q.filter(mobile=login_vo.mobile)
        else:
            raise MyException(ErrorCode.PARAM_ERROR)
        user = await q.first()
        if not user:
            raise MyException(ErrorCode.ACCOUNT_NOT_EXIST)
        error_count = await self.redis_util.User.get_user_error_count(user.id)
        if error_count >= self.MAX_ERROR_TIMES:
            raise MyException(ErrorCode.ACCOUNT_IS_FORBIDDEN)
        if login_vo.password:
            # 密码登录
            if not EncryptUtil.equals(login_vo.password, user.password):
                error_count = await self.redis_util.User.incr_user_error_count(user.id)
                if error_count >= self.MAX_ERROR_TIMES:  # 登录错误次数超过10次
                    if user.email:
                        # 给绑定的邮件发送解封邮件
                        random_code = RandomUtil.uuid4()
                        unblock_url = self.UNBLOCK_LOGIN_URL.format(random_code)
                        # 禁止登录
                        now = datetime.datetime.now()
                        end_time = now + datetime.timedelta(minutes=30)
                        async with transactions.in_transaction():
                            user_restrict = await UserRestriction.create(user_id=user.id,
                                                                         restrict_type=UserRestrictionTypeEnum.BAN,
                                                                         start_time=now,
                                                                         end_time=end_time)
                            key = f"{user_restrict.id}:{user.id}"
                            await self.redis_util.User.add_unlock_key(random_code, key)
                            await self.kafka_util.send_email(user.email, EmailConstant.RESET_ERROR_LOGIN_TITLE,
                                                             EmailConstant.RESET_ERROR_LOGIN_CONTENT.format(
                                                                 end_time.strftime("%Y-%m-%d %H:%M:%S"),
                                                                 unblock_url))
                    raise MyException(ErrorCode.ACCOUNT_IS_FORBIDDEN)
                raise MyException(ErrorCode.PASSWORD_ERROR)
        elif not await self.redis_util.VerifyCode.check_verify_code(login_vo.mobile, login_vo.code,
                                                                    VerifyCodeTypeEnum.LOGIN):
            # 验证码登录
            raise MyException(ErrorCode.CODE_VERIFY_ERROR)
        user_restriction_dto = await self._check_user_restriction(user)
        if user_restriction_dto.user_forbidden:
            raise MyException(ErrorCode.ACCOUNT_IS_FORBIDDEN)
        user.last_login_ip = IpUtil.get_ip_address(request)
        user.address = IpUtil.get_address_from_request(request)
        user.last_login_time = datetime.datetime.now()
        await asyncio.gather(
            self.redis_util.User.delete_user_error_count(user.id),
            user.save(update_fields=("last_login_ip", "address", "last_login_time"))
        )
        token = TokenUtil.create_token(user.id, user.username)
        return {"token": token}

    @staticmethod
    async def _check_user_restriction(user: User) -> UserRestrictionDTO:
        """
        用户限制检查
        """
        user_restriction_dto = UserRestrictionDTO()
        user_restrictions = await UserRestriction.filter(user_id=user.id, is_cancel=False).all()
        now = datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai"))
        update_list = []
        for user_restriction in user_restrictions:
            if not (user_restriction.is_forever or user_restriction.start_time <= now <= user_restriction.end_time):
                user_restriction.is_cancel = True
                user_restriction.cancel_time = now
                user_restriction.cancel_reason = "超过封禁时间，自动解除"
                update_list.append(user_restriction)
                continue
            match user_restriction.restrict_type:
                case UserRestrictionTypeEnum.BAN:  # 封禁
                    user.user_forbidden = True
                    user_restriction_dto.user_forbidden = True
                case UserRestrictionTypeEnum.MUTE:  # 禁言
                    user.comment_forbidden = True
                    user_restriction_dto.comment_forbidden = True
        if update_list:
            await UserRestriction.bulk_update(update_list, fields=("is_cancel", "cancel_time", "cancel_reason"),
                                              batch_size=500)
        return user_restriction_dto

    async def info(self):
        """
         获取自身用户信息
         :return UserInfoDTO
        """
        user_id = ContextVars.token_user_id.get()
        user = await User.filter(id=user_id).first()
        if not user:
            raise MyException(ErrorCode.ACCOUNT_NOT_EXIST)
        user.user_restriction = UserRestrictionDTO()
        dto = UserInfoDTO.model_validate(user, from_attributes=True)
        dto.email = DesensitizedUtil.email(dto.email)
        dto.mobile = DesensitizedUtil.mobile_phone(dto.mobile)
        dto.wechat = DesensitizedUtil.password(dto.wechat)
        (
            dto.article_collect_set,
            dto.article_like_set,
            dto.comment_like_set,
            dto.user_restriction
        ) = await asyncio.gather(
            self.redis_util.User.get_user_collect_articles(user_id),
            self.redis_util.User.get_user_like_articles(user_id),
            self.redis_util.User.get_user_like_comments(user_id),
            self._check_user_restriction(user)
        )
        # 获取用户配置
        dto.user_settings = await self.user_dao.get_user_settings(user_id)
        return dto

    async def unblock(self, key: str):
        value = await self.redis_util.User.get_unlock_key(key)
        if not value:
            return
        restrict_id, user_id = value
        await self.redis_util.User.delete_user_error_count(user_id)
        await UserRestriction.filter(id=restrict_id).update(is_cancel=True,
                                                            cancel_time=datetime.datetime.now(),
                                                            cancel_reason="用户点击邮件链接解封")
        await self.redis_util.User.delete_unlock_key(key)

    async def _fill_register_base_info(self, user: User, request: Request, register_vo: RegisterVO):
        """
        填充注册基础信息
        """

        user.username = register_vo.username
        user.nickname = register_vo.nickname
        user.password = EncryptUtil.encrypt(register_vo.password)
        user.occupation = "初来乍到"
        user.user_tag = UserTagEnum.NORMAL_USER
        user.last_login_ip = IpUtil.get_ip_address(request)
        user.address = IpUtil.get_address_from_request(request)
        user.summary = "这个人很懒，什么都没有留下"
        user.uid, user.avatar, user.background = await asyncio.gather(
            self.redis_util.User.gen_uid(),
            self.picture_util.get_random_img_url(avatar=True),
            self.picture_util.get_random_img_url())
        user.gender = GenderEnum.SECRET

    async def email_register(self, register_vo: RegisterVO):
        """
         用户邮箱注册
         :param register_vo RegisterVO
         :return token
        """
        request = ContextVars.request.get()
        if not register_vo.email or not register_vo.code:
            raise MyException(ErrorCode.PARAM_ERROR)
        if not await self.redis_util.VerifyCode.check_verify_code(register_vo.email, register_vo.code,
                                                                  VerifyCodeTypeEnum.REGISTER):
            raise MyException(ErrorCode.CODE_VERIFY_ERROR)
        exist_user = await User.filter(username=register_vo.username, email=register_vo.email).exists()
        if exist_user:
            raise MyException(ErrorCode.ACCOUNT_HAS_EXIST)
        user = User()
        user.email = register_vo.email
        await self._fill_register_base_info(user, request, register_vo)
        await asyncio.gather(
            user.save(),
            self.redis_util.VerifyCode.delete_verify_code(register_vo.email, VerifyCodeTypeEnum.REGISTER)
        )
        asyncio.create_task(self._send_notice(user))
        token = TokenUtil.create_token(user.id, user.username)
        return {"token": token}

    async def mobile_register(self, register_vo: RegisterVO):
        """
         用户手机号注册
         :param register_vo RegisterVO
         :return token
        """
        request = ContextVars.request.get()
        if not register_vo.mobile or not register_vo.code:
            raise MyException(ErrorCode.PARAM_ERROR)
        if not await self.redis_util.VerifyCode.check_verify_code(register_vo.mobile, register_vo.code,
                                                                  VerifyCodeTypeEnum.REGISTER):
            raise MyException(ErrorCode.CODE_VERIFY_ERROR)
        exist_user = await User.filter(mobile=register_vo.mobile).exists()
        if exist_user:
            raise MyException(ErrorCode.ACCOUNT_HAS_EXIST)
        user = User()
        user.mobile = register_vo.mobile
        await self._fill_register_base_info(user, request, register_vo)
        await asyncio.gather(
            user.save(),
            self.redis_util.VerifyCode.delete_verify_code(register_vo.mobile, VerifyCodeTypeEnum.REGISTER)
        )
        asyncio.create_task(self._send_notice(user))
        token = TokenUtil.create_token(user.id, user.username)
        return {"token": token}

    async def get_user_info(self, query_id: int, by_uid=False):
        """
        获取某一用户信息
        :param query_id: user_id/uid
        :param by_uid:
        :return:
        """
        login_user_id = ContextVars.token_user_id.get()
        if by_uid:
            user = await User.filter(uid=query_id).first()
        else:
            user = await User.filter(id=query_id).first()
        if not user:
            raise MyException(ErrorCode.ACCOUNT_NOT_EXIST)
        user_id = user.id
        dto = UserCommonInfoDTO.model_validate(user, from_attributes=True)
        dto.register_timestamp = user.register_time.timestamp()
        # 获取评论数量
        (
            dto.comment_count,
            dto.article_count,
            dto.view_count,
            dto.is_followed,
            dto.is_my_fans,
            dto.fans_count,
            dto.is_friend,
            dto.is_blocked
        ) = await asyncio.gather(
            Comment.filter(user_id=user_id, status=CommentStatusEnum.PASS).count(),  # 获取评论数量
            Article.filter(user_id=user_id, status=ArticleStatusEnum.PUBLISHED, is_deleted=False).count(),  # 获取文章数量
            self.redis_util.User.get_view_count(user_id),
            self.redis_util.Action.is_followed(login_user_id, user_id),  # 获取粉丝信息
            self.redis_util.Action.is_fans(login_user_id, user_id),
            self.redis_util.Action.get_fans_count(user_id),
            self.chat_dao.is_friend(login_user_id, user_id),
            self.chat_dao.is_blocked(login_user_id, user_id)
        )
        my_article_ids = await Article.filter(user_id=user_id, is_deleted=False).values_list("id", flat=True)
        # 获取成就相关信息
        (
            dto.article_view_count,
            dto.article_comment_count,
            dto.article_like_me_count,
            dto.article_collect_count
        ) = await asyncio.gather(
            self.redis_util.Article.get_articles_view_count(my_article_ids),
            self.redis_util.Article.get_articles_comment_count(my_article_ids),
            self.redis_util.Article.get_articles_like_count(my_article_ids),
            self.redis_util.Article.get_articles_collect_count(my_article_ids)
        )
        # 获取用户配置
        dto.user_settings = await self.user_dao.get_user_common_settings(user_id)
        return dto

    async def add_view_count(self, add_user_view_count_vo: AddUserViewCountVO):
        """
        增加用户访问量
        :param add_user_view_count_vo:
        :return:
        """
        await self.redis_util.User.add_view_count(add_user_view_count_vo.user_id)

    async def change_password_by_find(self, forget_password_vo: ForgetPasswordVO):
        """
        通过找回密码修改密码
        """
        if forget_password_vo.email:
            key = "email"
            value = forget_password_vo.email
            check = forget_password_vo.email
        elif forget_password_vo.mobile:
            key = "mobile"
            value = forget_password_vo.mobile
            check = forget_password_vo.mobile
        else:
            raise MyException(ErrorCode.PARAM_ERROR)
        if not await self.redis_util.VerifyCode.check_verify_code(check, forget_password_vo.code,
                                                                  VerifyCodeTypeEnum.FIND_PASSWORD):
            raise MyException(ErrorCode.CODE_VERIFY_ERROR)
        await asyncio.gather(
            User.filter(**{key: value}).update(password=EncryptUtil.encrypt(forget_password_vo.password)),
            self.redis_util.VerifyCode.delete_verify_code(check, VerifyCodeTypeEnum.FIND_PASSWORD)
        )

    async def change_password_by_login(self, change_password_vo: ChangePasswordVO):
        """
        通过登录修改密码
        :param change_password_vo ChangePasswordVO
        """
        user_id = ContextVars.token_user_id.get()
        user = await User.filter(id=user_id).first()
        if not user:
            raise MyException(ErrorCode.ACCOUNT_NOT_EXIST)
        match change_password_vo.change_type:
            case ChangePasswordTypeEnum.OLD_PASSWORD:
                if not EncryptUtil.equals(change_password_vo.old_password, user.password):
                    raise MyException(ErrorCode.PASSWORD_ERROR)
            case ChangePasswordTypeEnum.EMAIL_CODE:
                if not await self.redis_util.VerifyCode.check_verify_code(user.email, change_password_vo.code,
                                                                          VerifyCodeTypeEnum.CHANGE_PASSWORD):
                    raise MyException(ErrorCode.CODE_VERIFY_ERROR)
                await self.redis_util.VerifyCode.delete_verify_code(user.email, VerifyCodeTypeEnum.CHANGE_PASSWORD)
            case ChangePasswordTypeEnum.MOBILE_CODE:
                if not await self.redis_util.VerifyCode.check_verify_code(user.mobile, change_password_vo.code,
                                                                          VerifyCodeTypeEnum.CHANGE_PASSWORD):
                    raise MyException(ErrorCode.CODE_VERIFY_ERROR)
                await self.redis_util.VerifyCode.delete_verify_code(user.mobile, VerifyCodeTypeEnum.CHANGE_PASSWORD)
            case ChangePasswordTypeEnum.WECHAT_SCAN:
                open_id = await self.redis_util.Wechat.get_random_code_openid(change_password_vo.random_code)
                if user.wechat != open_id:
                    raise MyException(ErrorCode.WECHAT_NOT_SCAN)
                await self.redis_util.Wechat.delete_random_code(change_password_vo.random_code)
        user.password = EncryptUtil.encrypt(change_password_vo.password)
        await user.save(update_fields=("password",))

    async def update_user_info(self, user_update_vo: UserUpdateVO):
        """
        更新用户信息
        :param user_update_vo:
        """
        user_id = ContextVars.token_user_id.get()
        await User.filter(id=user_id).update(**user_update_vo.model_dump(exclude_none=True))
        self.event_server.emit(EventName.UPDATE_USER_INFO, user_id)

    async def save_user_settings(self, user_settings: UserSettingsType):
        """
        保存用户设置
        :param user_settings:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        db_user_settings = await UserSettings.filter(user_id=user_id, setting_key__in=user_settings.keys())
        db_user_settings_dict = {item.setting_key: item for item in db_user_settings}
        exists_user_settings = [item.setting_key for item in db_user_settings]
        save_items = []
        update_items = []
        for key, value in user_settings.items():
            if key not in exists_user_settings:
                item = UserSettings(user_id=user_id, setting_key=key, setting_value=value)
                save_items.append(item)
            else:
                item = db_user_settings_dict.get(key)
                if item.setting_value != value:
                    item.setting_value = value
                    update_items.append(item)
        async with transactions.in_transaction():
            if save_items:
                await UserSettings.bulk_create(save_items)
            if update_items:
                await UserSettings.bulk_update(update_items, ["setting_value"])

    async def change_email_bind(self, change_email_bind_vo: ChangeEmailBindVO):
        """
        修改邮箱绑定
        :param change_email_bind_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        exist_user = await User.filter(email=change_email_bind_vo.email).exists()
        if exist_user:
            raise MyException(ErrorCode.EMAIL_HAS_EXISTS)
        user = await User.filter(id=user_id).first()
        # 验证旧邮箱验证码
        if user.email and not await self.redis_util.VerifyCode.check_verify_code(user.email,
                                                                                 change_email_bind_vo.old_code,
                                                                                 VerifyCodeTypeEnum.CHANGE_BIND):
            raise MyException(ErrorCode.CODE_VERIFY_ERROR)
        # 验证新邮箱验证码
        if not await self.redis_util.VerifyCode.check_verify_code(change_email_bind_vo.email,
                                                                  change_email_bind_vo.code,
                                                                  VerifyCodeTypeEnum.CHANGE_BIND):
            raise MyException(ErrorCode.CODE_VERIFY_ERROR)
        user.email = change_email_bind_vo.email
        await user.save(update_fields=("email",))
        await asyncio.gather(
            self.redis_util.VerifyCode.delete_verify_code(user.email, VerifyCodeTypeEnum.CHANGE_BIND),
            self.redis_util.VerifyCode.delete_verify_code(change_email_bind_vo.email,
                                                          VerifyCodeTypeEnum.CHANGE_BIND)
        )

    async def change_mobile_bind(self, change_mobile_bind_vo: ChangeMobileBindVO):
        """
        修改手机绑定
        :param change_mobile_bind_vo:
        :return:
        """
        exist_user = await User.filter(mobile=change_mobile_bind_vo.mobile).exists()
        if exist_user:
            raise MyException(ErrorCode.MOBILE_HAS_EXISTS)
        user_id = ContextVars.token_user_id.get()
        user = await User.filter(id=user_id).first()
        # 验证旧手机号验证码
        if user.mobile and not await self.redis_util.VerifyCode.check_verify_code(user.mobile,
                                                                                  change_mobile_bind_vo.old_code,
                                                                                  VerifyCodeTypeEnum.CHANGE_BIND):
            raise MyException(ErrorCode.CODE_VERIFY_ERROR)
        # 验证新手机号验证码
        if not await self.redis_util.VerifyCode.check_verify_code(change_mobile_bind_vo.mobile,
                                                                  change_mobile_bind_vo.code,
                                                                  VerifyCodeTypeEnum.CHANGE_BIND):
            raise MyException(ErrorCode.CODE_VERIFY_ERROR)
        user.mobile = change_mobile_bind_vo.mobile
        await user.save(update_fields=("mobile",))
        await asyncio.gather(
            self.redis_util.VerifyCode.delete_verify_code(user.mobile, VerifyCodeTypeEnum.CHANGE_BIND),
            self.redis_util.VerifyCode.delete_verify_code(change_mobile_bind_vo.mobile,
                                                          VerifyCodeTypeEnum.CHANGE_BIND)
        )

    async def wechat_register(self, register_vo: RegisterVO):
        """
        微信注册
        :param register_vo:
        :return:
        """
        request = ContextVars.request.get()
        open_id = await self.redis_util.Wechat.get_random_code_openid(register_vo.code)
        if not open_id:
            raise MyException(ErrorCode.WECHAT_VERIFY_TIMEOUT)
        if await User.filter(Q(username=register_vo.username) | Q(wechat=register_vo.code)).exists():
            raise MyException(ErrorCode.ACCOUNT_HAS_EXIST)
        user = User()
        user.wechat = open_id
        await self._fill_register_base_info(user, request, register_vo)
        await asyncio.gather(
            user.save(),
            self.redis_util.Wechat.delete_random_code_openid(register_vo.code)
        )
        asyncio.create_task(self._send_notice(user))
        token = TokenUtil.create_token(user.id, user.username)
        return {"token": token}

    async def get_wechat_applet_code(self, code_type: WechatCodeTypeEnum):
        """
        获取微信小程序码
        :param code_type: WechatCodeTypeEnum
        :return:
        """
        code = self.wechat_util.get_random_code(code_type.value)
        result = await self.wechat_util.get_applet_code(code)
        await self.redis_util.Wechat.save_random_code_openid(code, "")
        ret = {"code": code, "img": result}
        return ret

    async def check_scan(self, code: str):
        """
        验证是否已经扫码
        :param code:
        :return:
        """
        dto = WechatScanResultDTO()
        if not await self.redis_util.Wechat.exist_random_code_openid(code):
            dto.status = WechatScanResultEnum.EXPIRED
            return dto
        open_id = await self.redis_util.Wechat.get_random_code_openid(code)
        if open_id:
            user = await User.filter(wechat=open_id).first()
            if user:
                token = TokenUtil.create_token(user.id, user.username)
                dto.status = WechatScanResultEnum.HAS_BIND
                dto.token = token
                await self.redis_util.Wechat.delete_random_code_openid(code)
            else:
                dto.status = WechatScanResultEnum.UNBIND
        else:
            dto.status = WechatScanResultEnum.NOT_SCAN
        return dto

    async def check_old_scan(self, code: str):
        """
        换绑微信验证旧微信
        :param code:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        dto = WechatScanResultDTO()
        if not await self.redis_util.Wechat.exist_random_code_openid(code):
            dto.status = WechatScanResultEnum.EXPIRED
            return dto
        open_id = await self.redis_util.Wechat.get_random_code_openid(code)
        if open_id:
            user = await User.filter(id=user_id).first()
            if user and user.wechat == open_id:
                # 已绑定,验证成功
                dto.status = WechatScanResultEnum.HAS_BIND
                await self.redis_util.Wechat.delete_random_code_openid(code)
            else:
                dto.status = WechatScanResultEnum.UNBIND
        else:
            dto.status = WechatScanResultEnum.NOT_SCAN
        return dto

    async def check_change_password_scan(self, code: str):
        """
        修改密码验证微信
        :param code:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        dto = WechatScanResultDTO()
        if not await self.redis_util.Wechat.exist_random_code_openid(code):
            dto.status = WechatScanResultEnum.EXPIRED
            return dto
        open_id = await self.redis_util.Wechat.get_random_code_openid(code)
        if open_id:
            user = await User.filter(id=user_id).first()
            if user and user.wechat == open_id:
                # 已绑定,验证成功
                dto.status = WechatScanResultEnum.HAS_BIND
                # 这里先不删除验证码，修改密码时再次验证并删除
            else:
                dto.status = WechatScanResultEnum.UNBIND
        else:
            dto.status = WechatScanResultEnum.NOT_SCAN
        return dto

    async def scan_callback(self, code: str, state: str):
        """
        微信扫码成功获取用户信息
        :param code: 服务器随机生成的code
        :param state: 登录凭证code
        :return:
        """
        open_id = await self.redis_util.Wechat.get_wechat_code_openid(state)
        if not open_id:
            open_id = await self.wechat_util.get_open_id(state)
        if not open_id:
            return
        await self.redis_util.Wechat.save_random_code_openid(code, open_id, datetime.timedelta(minutes=10))

    async def bind_wechat(self, wechat_bind_params_vo: WechatBindParamsVO):
        """
        换绑微信
        :param wechat_bind_params_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        open_id = await self.redis_util.Wechat.get_random_code_openid(wechat_bind_params_vo.code)
        if not open_id:
            raise MyException(ErrorCode.PARAM_ERROR)
        user = await User.filter(id=user_id).first()
        if user.wechat:
            # 已经绑定过微信, 验证旧微信是否通过验证
            wechat_open_id = await self.redis_util.Wechat.get_random_code_openid(wechat_bind_params_vo.old_code)
            if not wechat_open_id:
                raise MyException(ErrorCode.PARAM_ERROR)
        user.wechat = open_id
        await user.save(update_fields=("wechat",))
        await asyncio.gather(
            self.redis_util.Wechat.delete_random_code_openid(wechat_bind_params_vo.old_code),
            self.redis_util.Wechat.delete_random_code_openid(wechat_bind_params_vo.code)
        )

    async def get_wechat_user_info(self, code: str):
        """
        获取微信用户信息
        :param code: 微信登录获取的code
        :return:
        """
        await asyncio.sleep(1)
        open_id = await self.redis_util.Wechat.get_wechat_code_openid(code)
        if not open_id:
            open_id = await self.wechat_util.get_open_id(code)
        if not open_id:
            raise MyException(ErrorCode.PARAM_ERROR)
        await self.redis_util.Wechat.save_wechat_code_openid(code, open_id)
        user = await User.filter(wechat=open_id).first()
        if not user:
            raise MyException(ErrorCode.ACCOUNT_NOT_EXIST)
        dto = UserBaseInfoDTO.model_validate(user, from_attributes=True)
        return dto

    async def _send_notice(self, user: User):
        notice_dto = NoticeSaveDTO()
        notice_dto.title = "欢迎加入心悦心享"
        notice_dto.content = f"Hi~ {user.nickname}，在这里你可以发布你的文章、图片等，分享生活中的点点滴滴，希望你能喜欢❤️"
        notice_dto.notice_type = NoticeTypeEnum.SYSTEM
        notice_dto.user_id = user.id
        await self.kafka_util.send_notice(notice_dto)
        notice_dto.detail.from_user = await manager.get_user_info(user.id, UserBaseInfoDTO)
        await manager.send_message(WSMessageDTO[NoticeSaveDTO](message=notice_dto))
