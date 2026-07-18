from pydantic import Field

from apps.web.vo.base_vo import BaseVO


class NoteFolderVO(BaseVO):
    """笔记文件夹新增或重命名参数。"""

    name: str = Field(min_length=1)
    parent_id: int | None = None


class NoteFolderSortVO(BaseVO):
    """笔记文件夹排序参数。"""

    folder_ids: list[int] = Field(min_length=1)
