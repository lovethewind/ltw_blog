# @Time    : 2024/10/18 15:22
# @Author  : frank
# @File    : sms_util.py
import json

from alibabacloud_dysmsapi20170525.models import SendSmsRequest
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client

from apps.base.core.depend_inject import Component, Value, logger, RefreshScope


@Component()
@RefreshScope("aliyun.sms")
class SmsUtil:
    access_key: str = Value("aliyun.sms.access-key")
    secret_key: str = Value("aliyun.sms.secret-key")
    sign_name: str = Value("aliyun.sms.sign-name")
    endpoint: str = Value("aliyun.sms.endpoint")
    region: str = Value("aliyun.sms.region")

    def __init__(self):
        config = open_api_models.Config(
            access_key_id=self.access_key,
            # 必填，请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_SECRET。,
            access_key_secret=self.secret_key,
            endpoint=self.endpoint,
            region_id=self.region
        )
        self.client = Dysmsapi20170525Client(config)

    async def send_sms(self, message: dict[str, str]):
        mobile = message.get("mobile")
        sms_type = message.get("sms_type")
        code = message.get("code")
        send_sms_request = SendSmsRequest(
            phone_numbers=mobile,
            sign_name=self.sign_name,
            template_code=sms_type,
            template_param=json.dumps({"code": code})
        )
        try:
            self.client.send_sms_with_options(send_sms_request, util_models.RuntimeOptions())
        except Exception as error:
            logger.info(f"发送短信失败: {error}")
