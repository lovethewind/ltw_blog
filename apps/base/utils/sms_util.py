# @Time    : 2024/10/18 15:22
# @Author  : frank
# @File    : sms_util.py
import json

from alibabacloud_credentials import models as credential_models
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_dypnsapi20170525 import models as dypnsapi_models
from alibabacloud_dypnsapi20170525.client import Client as Dypnsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models

from apps.base.core.depend_inject import Component, RefreshScope, Value, logger


@Component()
@RefreshScope("aliyun.sms")
class SmsUtil:
    access_key: str = Value("aliyun.sms.access-key")
    secret_key: str = Value("aliyun.sms.secret-key")
    sign_name: str = Value("aliyun.sms.sign-name")
    endpoint: str = Value("aliyun.sms.endpoint")
    VERIFY_CODE_EXPIRE_MINUTES = 15

    def __init__(self) -> None:
        """初始化阿里云短信验证码客户端。

        :return: None。
        """
        credential = CredentialClient(
            credential_models.Config(
                type="access_key",
                access_key_id=self.access_key,
                access_key_secret=self.secret_key,
            )
        )
        config = open_api_models.Config(
            credential=credential,
            endpoint=self.endpoint,
        )
        self.client = Dypnsapi20170525Client(config)

    async def send_sms(self, message: dict[str, str]) -> None:
        """发送短信验证码。

        :param message: 包含手机号、模板编码和验证码的消息。
        :return: None。
        """
        mobile = message.get("mobile")
        sms_type = message.get("sms_type")
        code = message.get("code")
        if not mobile or not sms_type or not code:
            logger.error("短信验证码参数不完整")
            return
        send_sms_request = dypnsapi_models.SendSmsVerifyCodeRequest(
            phone_number=mobile,
            sign_name=self.sign_name,
            template_code=sms_type,
            template_param=json.dumps(
                {"code": code, "min": self.VERIFY_CODE_EXPIRE_MINUTES},
                ensure_ascii=False,
            ),
        )
        try:
            response = await self.client.send_sms_verify_code_with_options_async(
                send_sms_request,
                util_models.RuntimeOptions(),
            )
            if getattr(response.body, "code", None) != "OK":
                logger.error(
                    f"发送短信验证码失败，错误码: {getattr(response.body, 'code', None)}，"
                    f"错误信息: {getattr(response.body, 'message', None)}"
                )
            else:
                logger.info(f"发送短信验证码成功: {mobile}")
        except Exception as error:
            logger.exception(f"发送短信验证码异常: {error}")
