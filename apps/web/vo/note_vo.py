from pydantic import Field, field_validator

from apps.web.vo.base_vo import BaseVO


class NoteQueryVO(BaseVO):
    """笔记列表查询参数。"""

    keyword: str | None = Field(default=None, max_length=100)
    folder_id: int | None = None
    tag_id: int | None = None
    is_pinned: bool | None = None
    is_deleted: bool = False


class NoteCreateVO(BaseVO):
    """笔记创建参数。"""

    title: str | None = Field(default=None, max_length=100)
    content: str = ""
    folder_id: int | None = None
    tag_ids: list[int] = Field(default_factory=list)


class NoteUpdateVO(BaseVO):
    """笔记更新参数。"""

    title: str | None = Field(default=None, max_length=100)
    content: str | None = None
    folder_id: int | None = None
    tag_ids: list[int] | None = None

    @field_validator("title", "content", "tag_ids", mode="before")
    @classmethod
    def validate_non_nullable_fields(cls, value: object) -> object:
        """
        拒绝更新请求中显式传入的空标题、内容或标签列表。

        省略字段时，Pydantic 不会执行该验证器，因此仍可用于部分更新。

        :param value: 请求中传入的字段值。
        :return: 已验证的字段值。
        :raises ValueError: 字段显式传入 null 时抛出。
        """
        if value is None:
            raise ValueError("更新字段不允许为 null")
        return value


class NotePinVO(BaseVO):
    """笔记置顶状态参数。"""

    is_pinned: bool
