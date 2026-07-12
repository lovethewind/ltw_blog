from pydantic import Field

from apps.admin.vo.base_vo import BaseVO


class AdminCheckStatusVO(BaseVO):
    """
    后台审核状态更新参数。
    """

    status: int = Field(ge=1, le=3)
