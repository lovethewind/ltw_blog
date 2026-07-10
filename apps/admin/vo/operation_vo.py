from datetime import datetime

from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminJobQueryVO(BaseVO):
    """
    后台定时任务查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    group: str | None = Field(default=None, max_length=64)
    status: int | None = Field(default=None, ge=1, le=2)


class AdminJobCreateVO(BaseVO):
    """
    后台定时任务创建参数。
    """

    name: str = Field(min_length=1, max_length=64)
    group: str = Field(default="DEFAULT", min_length=1, max_length=64)
    invoke_target: str = Field(min_length=1, max_length=500)
    cron_expression: str = Field(min_length=1, max_length=255)
    misfire_policy: int = Field(default=3, ge=1, le=3)
    concurrent: bool = False
    status: int = Field(default=2, ge=1, le=2)
    create_user_id: int
    update_user_id: int | None = None
    description: str | None = Field(default=None, max_length=1000)


class AdminJobUpdateVO(BaseVO):
    """
    后台定时任务更新参数。
    """

    name: str | None = Field(default=None, min_length=1, max_length=64)
    group: str | None = Field(default=None, min_length=1, max_length=64)
    invoke_target: str | None = Field(default=None, min_length=1, max_length=500)
    cron_expression: str | None = Field(default=None, min_length=1, max_length=255)
    misfire_policy: int | None = Field(default=None, ge=1, le=3)
    concurrent: bool | None = None
    status: int | None = Field(default=None, ge=1, le=2)
    update_user_id: int | None = None
    description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminJobUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 定时任务更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


class AdminJobStatusVO(BaseVO):
    """
    后台定时任务状态更新参数。
    """

    status: int = Field(ge=1, le=2)
    update_user_id: int | None = None


class AdminSourceQueryVO(BaseVO):
    """
    后台资源查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    user_id: int | None = None
    is_deleted: bool | None = None


class AdminSourceUpdateVO(BaseVO):
    """
    后台资源更新参数。
    """

    is_deleted: bool | None = None

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminSourceUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 资源更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


class AdminNoticeQueryVO(BaseVO):
    """
    后台通知查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    user_id: int | None = None
    notice_type: int | None = Field(default=None, ge=1, le=7)
    is_read: bool | None = None


class AdminNoticeUpdateVO(BaseVO):
    """
    后台通知更新参数。
    """

    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = None
    is_read: bool | None = None

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminNoticeUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 通知更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


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
