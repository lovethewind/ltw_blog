from pydantic import Field

from apps.admin.vo.base_vo import BaseVO


class AdminUploadSignatureVO(BaseVO):
    """
    后台上传签名参数。
    """

    file_name: str = Field(min_length=1, max_length=255)
    dir_type: str = Field(default="avatar", min_length=1, max_length=30)
