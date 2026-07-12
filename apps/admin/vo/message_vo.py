from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminMessageQueryVO(BaseVO):
    """
    后台留言查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    user_id: int | None = None
    parent_id: int | None = None


class AdminMessageUpdateVO(BaseVO):
    """
    后台留言更新参数。
    """

    nickname: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=100)
    content: str | None = None
    avatar: str | None = Field(default=None, max_length=300)
    address: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminMessageUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 留言更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self
