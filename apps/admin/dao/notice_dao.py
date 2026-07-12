from typing import Any

from sqlalchemy import or_, select

from apps.admin.dao.base_dao import _delete, _paginate, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.notice import Notice


@Component()
class AdminNoticeDao:
    """后台通知数据访问对象。"""

    async def list_notices(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        user_id: int | None = None,
        notice_type: int | None = None,
        is_read: bool | None = None,
    ) -> tuple[list[Notice], int]:
        """
        分页查询通知。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 通知关键词。
        :param user_id: 用户 ID。
        :param notice_type: 通知类型。
        :param is_read: 是否已读。
        :return: 通知列表和总数。
        """
        stmt = select(Notice)
        if keyword:
            stmt = stmt.where(or_(Notice.title.ilike(f"%{keyword}%"), Notice.content.ilike(f"%{keyword}%")))
        if user_id:
            stmt = stmt.where(Notice.user_id == user_id)
        if notice_type is not None:
            stmt = stmt.where(Notice.notice_type == notice_type)
        if is_read is not None:
            stmt = stmt.where(Notice.is_read == is_read)
        return await _paginate(stmt, current, size)

    async def get_notice_by_id(self, notice_id: int) -> Notice | None:
        """
        根据 ID 查询通知。

        :param notice_id: 通知 ID。
        :return: 通知对象。
        """
        return await db.model_first(select(Notice).where(Notice.id == notice_id))

    async def update_notice(self, notice: Notice, data: dict[str, Any]) -> Notice:
        """
        更新通知。

        :param notice: 通知对象。
        :param data: 更新数据。
        :return: 通知对象。
        """
        return await _update(notice, data)

    async def delete_notice(self, notice_id: int) -> None:
        """
        删除通知。

        :param notice_id: 通知 ID。
        :return: None。
        """
        await _delete(Notice, notice_id)
