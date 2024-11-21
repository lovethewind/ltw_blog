# @Time    : 2024/10/16 15:40
# @Author  : frank
# @File    : oss_vo.py
from apps.web.vo.base_vo import BaseVO


class GetSignatureVO(BaseVO):
    file_name: str
    dir_type: str
