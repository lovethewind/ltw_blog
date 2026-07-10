from pydantic import Field

from apps.admin.vo.base_vo import BaseVO


class AdminLoginVO(BaseVO):
    """
    后台登录请求参数。
    """

    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=1, max_length=30)
