from datetime import datetime

from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminUserRestrictionQueryVO(BaseVO):
    """
    后台用户限制查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    user_id: int | None = None
    restrict_type: int | None = Field(default=None, ge=1, le=2)
    is_cancel: bool | None = None


class AdminUserRestrictionCreateVO(BaseVO):
    """
    后台用户限制创建参数。
    """

    user_id: int
    restrict_type: int = Field(ge=1, le=2)
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_forever: bool = False
    reason: str | None = Field(default=None, max_length=1000)


class AdminUserRestrictionUpdateVO(BaseVO):
    """
    后台用户限制更新参数。
    """

    restrict_type: int | None = Field(default=None, ge=1, le=2)
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_forever: bool | None = None
    reason: str | None = Field(default=None, max_length=1000)
    is_cancel: bool | None = None
    cancel_time: datetime | None = None
    cancel_reason: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminUserRestrictionUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 用户限制更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


class AdminUserRestrictionCancelVO(BaseVO):
    """
    后台用户限制解除参数。
    """

    cancel_reason: str | None = Field(default=None, max_length=1000)
