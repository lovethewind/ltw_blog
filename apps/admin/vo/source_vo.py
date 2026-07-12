from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


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
