from pydantic import Field, field_validator, model_validator

from apps.admin.vo.base_vo import BaseVO
from apps.scheduler.core.cron import build_cron_trigger
from apps.scheduler.core.invoke import resolve_invoke_target


class JobScheduleValidationMixin:
    """定时任务调度字段校验。"""

    @field_validator("cron_expression", check_fields=False)
    @classmethod
    def validate_cron_expression(cls, value: str | None) -> str | None:
        """校验五段或六段式 Cron 表达式。

        :param value: Cron 表达式
        :return: 原 Cron 表达式
        :raises ValueError: Cron 表达式无效时抛出
        """
        if value is None:
            return value
        try:
            build_cron_trigger(value)
        except ValueError as exc:
            raise ValueError("Cron 表达式无效") from exc
        return value

    @field_validator("invoke_target", check_fields=False)
    @classmethod
    def validate_invoke_target(cls, value: str | None) -> str | None:
        """校验调用目标位于允许的 base service 中。

        :param value: 调用目标
        :return: 原调用目标
        :raises ValueError: 调用目标无效时抛出
        """
        if value is not None:
            resolve_invoke_target(value)
        return value


class AdminJobQueryVO(BaseVO):
    """
    后台定时任务查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    group: str | None = Field(default=None, max_length=64)
    status: int | None = Field(default=None, ge=1, le=2)
    create_user_id: int | None = None


class AdminJobCreateVO(JobScheduleValidationMixin, BaseVO):
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


class AdminJobUpdateVO(JobScheduleValidationMixin, BaseVO):
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
    create_user_id: int | None = None
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
