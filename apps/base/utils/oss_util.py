import datetime
import os
import uuid
from typing import Type
from urllib.parse import quote_plus

import oss2
from oss2 import Auth, AuthV4

from apps.base.core.depend_inject import Component, Value, RefreshScope, logger
from apps.base.enum.error_code import ErrorCode
from apps.base.enum.oss import DirType
from apps.base.exception.my_exception import MyException
from apps.web.dto.oss_dto import SignatureResultDTO


class UploadConfigInfo:

    def __init__(self, content_type: str, max_size: int, expire_seconds: int, old_filename: str, filename: str,
                 key: str):
        self.content_type = content_type
        self.max_size = max_size
        self.expire_seconds = expire_seconds
        self.old_filename = old_filename
        self.filename = filename
        self.key = key


@Component()
@RefreshScope("aliyun.oss")
class OssUtil:
    access_key: str = Value("aliyun.oss.access-key")
    secret_key: str = Value("aliyun.oss.secret-key")
    endpoint: str = Value("aliyun.oss.endpoint")
    region: str = Value("aliyun.oss.region")
    cdn_domain: str = Value("aliyun.oss.cdn-domain")
    bucket_name: str = Value("aliyun.oss.bucket")
    use_cdn_domain: bool = Value("aliyun.oss.use-cdn-domain")

    def __init__(self):
        auth: Auth | AuthV4 = oss2.AuthV4(self.access_key, self.secret_key)
        # 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
        self.bucket = oss2.Bucket(auth, endpoint=self.endpoint, bucket_name=self.bucket_name, region=self.region)

    def upload_file(self, file: bytes, name: str, dir_type: DirType = DirType.IMAGE):
        """
        上传文件
        :param file: 文件
        :param name: 文件名
        :param dir_type: 文件类型
        :return:
        """

        if not file or not name:
            raise MyException(ErrorCode.PARAM_ERROR, "文件(名)不能为空")
        upload_config_info = self._get_info(dir_type, name)
        key = upload_config_info.key
        try:
            ret = self.bucket.put_object(key, file)
            logger.info(f"上传文件结果: 文件名[{key}], code[{ret.status}], resp[{ret.resp}]")
            return f"{self.get_cname()}/{key}"
        except Exception as e:
            logger.error("上传文件失败", e)

    def get_signature(self, dir_type: Type[DirType], file_name: str) -> SignatureResultDTO:
        """
        获取上传文件签名
        :param dir_type: 前端传来的数据
        :param file_name: 前端传来的数据
        :return: 返回文件上传路径、contentType等
        """
        upload_config_info = self._get_info(dir_type, file_name)
        try:
            key = upload_config_info.key
            content_disposition = f"attachment; filename*=utf-8''{quote_plus(upload_config_info.old_filename)}"
            headers = {
                "content-type": upload_config_info.content_type,
                "content-disposition": content_disposition,
                "x-oss-forbid-overwrite": "true"
            }
            upload_url = self.bucket.sign_url("PUT", key, upload_config_info.expire_seconds,
                                              headers=headers,
                                              slash_safe=True)
            url = upload_url.split("?", 1)[0]
            signature_result = SignatureResultDTO(upload_url=upload_url,
                                                  url=url,
                                                  content_disposition=content_disposition,
                                                  content_type=upload_config_info.content_type)
            return signature_result
        except Exception as e:
            logger.error(f"获取签名失败: {e}")

    def _get_info(self, dir_type: Type[DirType], file_name: str) -> UploadConfigInfo:
        """
        根据前端传来的数据进行处理
        :param dir_type:
        :param file_name:
        :return: 返回文件上传路径、contentType等
        """
        dir_type = dir_type.value
        # 生成文件路径
        filename = file_name.replace(" ", "").replace("%", "")
        name, suffix = os.path.splitext(filename)
        new_filename = uuid.uuid4().hex + suffix
        date = datetime.datetime.now().strftime("%Y%m%d")
        new_file_path = os.path.join(dir_type.dir, date, new_filename)
        ret = UploadConfigInfo(dir_type.content_type,
                               dir_type.max_size,
                               dir_type.expire_seconds,
                               filename,
                               new_filename,
                               new_file_path)
        return ret

    def get_host(self):
        return "https://" + self.bucket_name + "." + self.endpoint

    def get_cname(self):
        if self.use_cdn_domain:
            return "https://" + self.cdn_domain
        return self.get_host()
