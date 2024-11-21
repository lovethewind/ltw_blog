# @Time    : 2024/10/16 15:55
# @Author  : frank
# @File    : oss_dto.py
from apps.web.dto.base_dto import BaseDTO


class SignatureResultDTO(BaseDTO):
    upload_url: str
    url: str
    content_disposition: str
    content_type: str
