import math
from collections.abc import Sequence

from apps.admin.dto.base_dto import BaseDTO


class AdminBaseService:
    """后台管理服务公共能力。"""

    def _normalize_description(self, data: dict[str, object]) -> None:
        """
        规范化描述字段。

        :param data: 保存数据
        :return: None
        """
        if "description" in data and data["description"] is None:
            data["description"] = ""

    def _fill_thumbnail_url(self, data: dict[str, object], source_field: str, thumb_field: str) -> None:
        """
        在未传缩略图时使用原图地址兜底。

        :param data: 保存数据。
        :param source_field: 原图字段名。
        :param thumb_field: 缩略图字段名。
        :return: None
        """
        if source_field in data and (not data.get(thumb_field)):
            data[thumb_field] = data[source_field]

    def _page_result(self, current: int, size: int, total: int, records: Sequence[BaseDTO]) -> dict:
        """
        构建分页响应。

        :param current: 当前页码
        :param size: 每页条数
        :param total: 总数
        :param records: 数据列表
        :return: 分页响应
        """
        return {
            "current": current,
            "pages": math.ceil(total / size) if size else 0,
            "records": records,
            "size": size,
            "total": total,
        }
