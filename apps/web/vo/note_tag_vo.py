from pydantic import Field

from apps.web.vo.base_vo import BaseVO


class NoteTagVO(BaseVO):
    """笔记标签新增或重命名参数。"""

    name: str = Field(min_length=1)
