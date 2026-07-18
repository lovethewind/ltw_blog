from datetime import datetime

from pydantic import Field

from apps.web.dto.base_dto import BaseDTO


class NoteFolderDTO(BaseDTO):
    """笔记文件夹响应数据。"""

    id: int
    name: str
    sort_order: int
    parent_id: int | None
    is_deleted: bool
    deleted_root_id: int | None


class NoteTagDTO(BaseDTO):
    """笔记标签响应数据。"""

    id: int
    name: str


class NoteListDTO(BaseDTO):
    """笔记列表响应数据。"""

    id: int
    title: str
    folder_id: int | None
    tag_list: list[NoteTagDTO] = Field(default_factory=list)
    is_pinned: bool
    update_time: datetime


class NoteDTO(NoteListDTO):
    """笔记详情响应数据。"""

    content: str
    create_time: datetime
    deleted_time: datetime | None


class NoteHistoryListDTO(BaseDTO):
    """笔记历史版本列表响应数据。"""

    id: int
    title: str
    content_preview: str
    create_time: datetime


class NoteHistoryDTO(BaseDTO):
    """笔记历史版本详情响应数据。"""

    id: int
    title: str
    content: str
    folder_id: int | None
    tag_ids: list[int] = Field(default_factory=list)
    create_time: datetime
