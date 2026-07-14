import datetime
import os
import uuid
from urllib.parse import quote_plus, unquote, urlsplit

import alibabacloud_oss_v2 as oss
import alibabacloud_oss_v2.aio as oss_aio

from apps.base.core.depend_inject import Component, RefreshScope, Value, logger
from apps.base.dto.oss_dto import SignatureResultDTO
from apps.base.enum.error_code import ErrorCode
from apps.base.enum.oss import DirType
from apps.base.exception.my_exception import MyException


class UploadConfigInfo:

    def __init__(
        self, content_type: str, max_size: int, expire_seconds: int, old_filename: str, filename: str, key: str
    ):
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
    https: bool = Value("aliyun.oss.https")

    def __init__(self) -> None:
        """
        初始化 OSS V2 客户端。

        :return: None
        """
        credentials_provider = oss.credentials.StaticCredentialsProvider(self.access_key, self.secret_key)
        config = oss.Config(
            region=self.region,
            endpoint=self.endpoint,
            signature_version="v4",
            credentials_provider=credentials_provider,
            disable_upload_crc64_check=True,
        )
        self.client = oss_aio.AsyncClient(config)
        self.presign_client = oss.Client(config)

    async def upload_file(self, file: bytes, name: str, dir_type: DirType = DirType.IMAGE) -> str | None:
        """
        上传文件

        :param file: 文件
        :param name: 文件名
        :param dir_type: 文件类型
        :return: 上传后的文件访问地址，上传失败时返回 None
        :raises MyException: 文件或文件名为空时抛出参数错误
        """

        if not file or not name:
            raise MyException(ErrorCode.PARAM_ERROR, "文件(名)不能为空")
        upload_config_info = self._get_info(dir_type, name)
        key = upload_config_info.key
        try:
            ret = await self.client.put_object(
                oss.PutObjectRequest(
                    bucket=self.bucket_name,
                    key=key,
                    body=file,
                    content_type=upload_config_info.content_type,
                    forbid_overwrite=True,
                )
            )
            logger.info(f"上传文件结果: 文件名[{key}], etag[{ret.etag}], hash_crc64[{ret.hash_crc64}]")
            return self.get_url(key)
        except Exception as e:
            logger.exception(f"上传文件失败: {e}")

    async def delete_file(self, url: str) -> None:
        """
        根据资源地址删除 OSS 文件。

        :param url: OSS 资源完整地址或对象 key。
        :return: None。
        :raises ValueError: 无法从资源地址解析对象 key 时抛出。
        """
        key = unquote(urlsplit(url).path).lstrip("/")
        if not key:
            raise ValueError("OSS 资源地址中缺少对象 key")
        await self.client.delete_object(oss.DeleteObjectRequest(bucket=self.bucket_name, key=key))
        logger.info(f"删除 OSS 文件成功: [{key}]")

    async def get_signature(self, dir_type: DirType, file_name: str) -> SignatureResultDTO:
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
            result = self.presign_client.presign(
                oss.PutObjectRequest(
                    bucket=self.bucket_name,
                    key=key,
                    content_type=upload_config_info.content_type,
                    content_disposition=content_disposition,
                    forbid_overwrite=True,
                ),
                expires=datetime.timedelta(seconds=upload_config_info.expire_seconds),
            )
            upload_url = result.url
            if not upload_url:
                raise MyException(ErrorCode.SERVICE_ERROR)
            signature_result = SignatureResultDTO(
                upload_url=upload_url,
                url=self.get_url(key),
                content_disposition=content_disposition,
                content_type=upload_config_info.content_type,
                signed_headers=dict(result.signed_headers or {}),
            )
            return signature_result
        except Exception as e:
            logger.error(f"获取签名失败: {e}")
            raise MyException(ErrorCode.SERVICE_ERROR)

    def _get_info(self, dir_type: DirType, file_name: str) -> UploadConfigInfo:
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
        ret = UploadConfigInfo(
            dir_type.content_type, dir_type.max_size, dir_type.expire_seconds, filename, new_filename, new_file_path
        )
        return ret

    def get_url(self, key: str) -> str:
        """
        生成外部访问用的完整 OSS 文件地址。

        :param key: OSS 对象 key。
        :return: 完整资源访问地址。
        """
        return f"{self.get_cname()}/{key.lstrip('/')}"

    def get_host(self) -> str:
        """
        获取 OSS bucket 默认访问域名。

        :return: OSS bucket 默认访问域名。
        """
        return "https://" + self.bucket_name + "." + self.endpoint

    def get_cname(self) -> str:
        """
        获取 OSS 资源访问域名，优先使用 CDN 域名。

        :return: OSS 资源访问域名。
        """
        if self.use_cdn_domain:
            prefix = "https" if self.https else "http"
            return f"{prefix}://{self.cdn_domain}"
        return self.get_host()
