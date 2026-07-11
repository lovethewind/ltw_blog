from pydantic import Field

from apps.base.dto.base_dto import BaseDTO


class SignatureResultDTO(BaseDTO):
    """
    OSS 上传签名结果 DTO。
    """

    upload_url: str
    url: str
    content_disposition: str
    content_type: str
    signed_headers: dict[str, str] = Field(default_factory=dict)
