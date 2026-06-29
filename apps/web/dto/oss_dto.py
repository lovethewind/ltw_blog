# @Time    : 2024/10/16 15:55
# @Author  : frank
# @File    : oss_dto.py
from pydantic import Field

from apps.web.dto.base_dto import BaseDTO


class SignatureResultDTO(BaseDTO):
    """
    OSS 上传签名结果。
    """

    upload_url: str
    url: str
    content_disposition: str
    content_type: str
    signed_headers: dict[str, str] = Field(default_factory=dict)
