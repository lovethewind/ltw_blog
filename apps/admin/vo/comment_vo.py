from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminCommentQueryVO(BaseVO):
    """
    后台评论查询参数。
    """

    current: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=100)
    obj_id: int | None = None
    obj_type: int | None = Field(default=None, ge=1, le=5)
    status: int | None = Field(default=None, ge=1, le=3)
    user_id: int | None = None


class AdminCommentUpdateVO(BaseVO):
    """
    后台评论更新参数。
    """

    content: str | None = None
    status: int | None = Field(default=None, ge=1, le=3)

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminCommentUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 评论更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self


class AdminCommentStatusVO(BaseVO):
    """
    后台评论状态更新参数。
    """

    status: int = Field(ge=1, le=3)
