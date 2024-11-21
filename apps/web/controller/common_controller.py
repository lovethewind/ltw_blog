# @Time    : 2024/9/14 16:50
# @Author  : frank
# @File    : common_controller.py
from fastapi import APIRouter

from apps.base.core.depend_inject import Controller, Autowired
from apps.base.utils.decorator_util import avoid_repeat_submit
from apps.base.utils.response_util import ResponseUtil
from apps.web.service.common_service import CommonService
from apps.web.vo.common_vo import EmailCodeVO, MobileCodeVO, FeedbackVO, UserEmailCodeVO, UserMobileCodeVO
from apps.web.vo.user_vo import ValidateAccountExistVO

router = APIRouter(prefix="/common", tags=["公共接口"])


@Controller(router)
class CommonController:
    common_service: CommonService = Autowired()

    @router.get("/common/getWebsiteViewCount", summary="获取网站访问量")
    async def get_website_view_count(self):
        """
        获取网站访问量
        :return:
        """
        ret = await self.common_service.get_website_view_count()
        return ResponseUtil.success(ret)

    @router.get("/common/addWebsiteViewCount", summary="增加网站访问量")
    async def add_website_view_count(self):
        """
        增加网站访问量
        :return:
        """
        await self.common_service.add_website_view_count()
        return ResponseUtil.success()

    @router.post("/common/getEmailCode", summary="获取邮箱验证码(无需登录)")
    async def get_email_code(self, email_code_vo: EmailCodeVO):
        """
        获取邮箱验证码(无需登录)
        :param email_code_vo:
        :return:
        """
        ret = await self.common_service.get_email_code(email_code_vo)
        return ResponseUtil.success(ret)

    @router.post("/getEmailCode", summary="获取邮箱验证码(需登录)")
    async def get_user_email_code(self, email_code_vo: UserEmailCodeVO):
        """
        获取邮箱验证码(需登录)
        :return:
        """
        ret = await self.common_service.get_user_email_code(email_code_vo)
        return ResponseUtil.success(ret)

    @router.post("/validEmailCode", summary="验证邮箱验证码")
    async def valid_user_email_code(self, email_code_vo: UserEmailCodeVO):
        """
        验证邮箱验证码
        :param email_code_vo:
        :return:
        """
        ret = await self.common_service.valid_user_email_code(email_code_vo)
        return ResponseUtil.success(ret)

    ################手机号相关#####################

    @router.post("/common/getMobileCode", summary="获取手机号验证码(无需登录)")
    @avoid_repeat_submit("获取手机号验证码重复提交")
    async def get_mobile_code(self, mobile_code_vo: MobileCodeVO):
        """
        获取手机号验证码(无需登录)
        :param mobile_code_vo:
        :return:
        """
        ret = await self.common_service.get_mobile_code(mobile_code_vo)
        return ResponseUtil.success(ret)

    @router.post("/getMobileCode", summary="获取手机号验证码(需登录)")
    async def get_user_mobile_code(self, mobile_code_vo: UserMobileCodeVO):
        """
        获取手机号验证码(需登录)
        :param mobile_code_vo:
        :return:
        """
        ret = await self.common_service.get_user_mobile_code(mobile_code_vo)
        return ResponseUtil.success(ret)

    @router.post("/common/validMobileCode", summary="验证手机号验证码(无需登录)")
    async def valid_mobile_code(self, mobile_code_vo: MobileCodeVO):
        """
        验证手机号验证码(无需登录)
        :param mobile_code_vo:
        :return:
        """
        ret = await self.common_service.valid_mobile_code(mobile_code_vo)
        return ResponseUtil.success(ret)

    @router.post("/validMobileCode", summary="验证手机号验证码(需登录)")
    async def valid_user_mobile_code(self, mobile_code_vo: UserMobileCodeVO):
        """
        验证手机号验证码(需登录)
        :param mobile_code_vo:
        :return:
        """
        ret = await self.common_service.valid_user_mobile_code(mobile_code_vo)
        return ResponseUtil.success(ret)

    ######################其他##########################

    @router.post("/common/validAccountExists", summary="验证账户是否已存在")
    async def valid_account_exists(self, validate_account_exist_vo: ValidateAccountExistVO):
        """
        验证账户是否已存在
        :param validate_account_exist_vo:
        :return:
        """
        ret = await self.common_service.valid_account_exists(validate_account_exist_vo)
        return ResponseUtil.success(ret)

    @router.post("/common/addFeedback", summary="用户反馈")
    async def add_feedback(self, feedback_vo: FeedbackVO):
        """
        用户反馈
        :param feedback_vo:
        :return:
        """
        await self.common_service.add_feedback(feedback_vo)
        return ResponseUtil.success()
