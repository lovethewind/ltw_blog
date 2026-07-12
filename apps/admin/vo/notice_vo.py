from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


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
