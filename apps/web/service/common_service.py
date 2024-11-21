# @Time    : 2024/9/14 16:50
# @Author  : frank
# @File    : common_service.py
from apps.base.constant.email_constant import EmailConstant
from apps.base.constant.sms_constant import SmsConstant
from apps.base.core.depend_inject import Component, Autowired
from apps.base.enum.common import VerifyCodeTypeEnum, FeedbackTypeEnum
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.user import User
from apps.base.utils.ip_util import IpUtil
from apps.base.utils.random_util import RandomUtil
from apps.base.utils.redis_util import RedisUtil
from apps.web.core.context_vars import ContextVars
from apps.web.core.kafka.util import KafkaUtil
from apps.web.vo.common_vo import EmailCodeVO, MobileCodeVO, FeedbackVO, UserEmailCodeVO, UserMobileCodeVO
from apps.web.vo.user_vo import ValidateAccountExistVO


@Component()
class CommonService:
    redis_util: RedisUtil = Autowired()
    kafka_util: KafkaUtil = Autowired()

    async def get_website_view_count(self):
        """
        获取网站访问量
        :return:
        """
        return await self.redis_util.Website.get_website_view_count()

    async def add_website_view_count(self):
        """
        增加网站访问量
        :return:
        """
        request = ContextVars.request.get()
        ip_address = IpUtil.get_ip_address(request)
        await self.redis_util.Website.incr_website_view_count(ip_address)

    async def get_email_code(self, email_code_vo: EmailCodeVO):
        """
        获取邮箱验证码(无需登录)
        :param email_code_vo:
        :return:
        """
        if email_code_vo.code_type == VerifyCodeTypeEnum.REGISTER:
            title = EmailConstant.REGISTER_TITLE
            content = EmailConstant.REGISTER_CONTENT
        elif email_code_vo.code_type == VerifyCodeTypeEnum.FIND_PASSWORD:
            title = EmailConstant.FIND_PASSWORD_TITLE
            content = EmailConstant.FIND_PASSWORD_CONTENT
        else:
            raise MyException(ErrorCode.PARAM_ERROR)
        email = email_code_vo.email
        code = RandomUtil.random_numbers(6)
        await self.kafka_util.send_email(email, title, content.format(code))
        await self.redis_util.VerifyCode.save_verify_code(email, code, email_code_vo.code_type)

    async def get_user_email_code(self, email_code_vo: UserEmailCodeVO):
        """
        获取邮箱验证码(需登录)
        :param email_code_vo:
        :return:
        """
        if email_code_vo.code_type == VerifyCodeTypeEnum.CHANGE_BIND:
            title = EmailConstant.CHANGE_BIND_TITLE
            content = EmailConstant.CHANGE_BIND_CONTENT
        elif email_code_vo.code_type == VerifyCodeTypeEnum.CHANGE_PASSWORD:
            title = EmailConstant.CHANGE_PASSWORD_TITLE
            content = EmailConstant.CHANGE_PASSWORD_CONTENT
        else:
            raise MyException(ErrorCode.PARAM_ERROR)
        user_id = ContextVars.token_user_id.get()
        user = await User.filter(id=user_id).first()
        code = RandomUtil.random_numbers(6)
        await self.kafka_util.send_email(user.email, title, content.format(code))
        await self.redis_util.VerifyCode.save_verify_code(user.email, code, email_code_vo.code_type)

    async def valid_user_email_code(self, email_code_vo: UserEmailCodeVO):
        """
        验证邮箱验证码(需登录)
        :param email_code_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        user = await User.filter(id=user_id).first()
        return await self.redis_util.VerifyCode.check_verify_code(user.email, email_code_vo.code,
                                                                  email_code_vo.code_type)

    async def get_mobile_code(self, mobile_code_vo: MobileCodeVO):
        """
        获取手机号验证码(无需登录)
        :param mobile_code_vo:
        :return:
        """
        mobile = mobile_code_vo.mobile
        code = RandomUtil.random_numbers(6)
        if mobile_code_vo.code_type == VerifyCodeTypeEnum.REGISTER:
            sms_type = SmsConstant.TYPE_REGISTER
        elif mobile_code_vo.code_type == VerifyCodeTypeEnum.LOGIN:
            sms_type = SmsConstant.TYPE_LOGIN
        elif mobile_code_vo.code_type == VerifyCodeTypeEnum.FIND_PASSWORD:
            sms_type = SmsConstant.TYPE_FIND_PASSWORD
        else:
            raise MyException(ErrorCode.PARAM_ERROR)
        await self.kafka_util.send_sms(mobile, sms_type, code)
        await self.redis_util.VerifyCode.save_verify_code(mobile, code, mobile_code_vo.code_type)

    async def get_user_mobile_code(self, mobile_code_vo: UserMobileCodeVO):
        """
        获取手机号验证码(需登录)
        :param mobile_code_vo:
        :return:
        """
        if mobile_code_vo.code_type == VerifyCodeTypeEnum.CHANGE_BIND:
            sms_type = SmsConstant.TYPE_CHANGE_BIND
        elif mobile_code_vo.code_type == VerifyCodeTypeEnum.CHANGE_PASSWORD:
            sms_type = SmsConstant.TYPE_CHANGE_PASSWORD
        else:
            raise MyException(ErrorCode.PARAM_ERROR)
        user_id = ContextVars.token_user_id.get()
        user = await User.filter(id=user_id).first()
        code = RandomUtil.random_numbers(6)
        await self.kafka_util.send_sms(user.mobile, sms_type, code)
        await self.redis_util.VerifyCode.save_verify_code(user.mobile, code, mobile_code_vo.code_type)

    async def valid_mobile_code(self, mobile_code_vo: MobileCodeVO):
        """
        验证手机号验证码(无需登录)
        :param mobile_code_vo:
        :return:
        """
        if mobile_code_vo.code_type not in (VerifyCodeTypeEnum.FIND_PASSWORD,
                                            VerifyCodeTypeEnum.REGISTER,
                                            VerifyCodeTypeEnum.LOGIN):
            raise MyException(ErrorCode.PARAM_ERROR)
        return await self.redis_util.VerifyCode.check_verify_code(mobile_code_vo.mobile, mobile_code_vo.code,
                                                                  mobile_code_vo.code_type)

    async def valid_user_mobile_code(self, mobile_code_vo: UserMobileCodeVO):
        """
        验证手机号验证码(需登录)
        :param mobile_code_vo:
        :return:
        """
        if mobile_code_vo.code_type not in (VerifyCodeTypeEnum.CHANGE_BIND,
                                            VerifyCodeTypeEnum.CHANGE_PASSWORD):
            raise MyException(ErrorCode.PARAM_ERROR)
        user_id = ContextVars.token_user_id.get()
        user = await User.filter(id=user_id).first()
        return await self.redis_util.VerifyCode.check_verify_code(user.mobile, mobile_code_vo.code,
                                                                  mobile_code_vo.code_type)

    async def valid_account_exists(self, validate_account_exist_vo: ValidateAccountExistVO):
        """
        验证账户是否已存在
        :param validate_account_exist_vo:
        :return:
        """
        query_dict = validate_account_exist_vo.model_dump(exclude_none=True)
        if not query_dict:
            raise MyException(ErrorCode.PARAM_ERROR)
        return await User.filter(**query_dict).exists()

    async def add_feedback(self, feedback_vo: FeedbackVO):
        """
        用户反馈
        :param feedback_vo:
        :return:
        """
        # 反馈暂时先发送至邮箱
        feedback_type = "需求" if feedback_vo.feedback_type == FeedbackTypeEnum.REQUIREMENT else "缺陷"
        content = f"""
        <html>
            <body>
                <p>用户邮箱: {feedback_vo.email}</p>
                <p>反馈类型: {feedback_type}</p>
                <p>需求: {feedback_vo.title}</p>
                <p>反馈内容: {feedback_vo.content}</p>
            </body>
        </html>
        """
        await self.kafka_util.send_email(EmailConstant.SELF_MAIL, f"心悦心享-用户反馈", content)
