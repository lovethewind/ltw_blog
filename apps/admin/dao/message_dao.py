from typing import Any

from sqlalchemy import or_, select

from apps.admin.dao.base_dao import _delete, _paginate, _update
from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.message import Message


@Component()
class AdminMessageDao:
    """后台留言数据访问对象。"""

    async def list_messages(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        user_id: int | None = None,
        parent_id: int | None = None,
    ) -> tuple[list[Message], int]:
        """
        分页查询留言。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 留言内容、昵称或邮箱关键词。
        :param user_id: 用户 ID。
        :param parent_id: 父留言 ID。
        :return: 留言列表和总数。
        """
        stmt = select(Message)
        if keyword:
            stmt = stmt.where(
                or_(
                    Message.content.ilike(f"%{keyword}%"),
                    Message.nickname.ilike(f"%{keyword}%"),
                    Message.email.ilike(f"%{keyword}%"),
                )
            )
        if user_id:
            stmt = stmt.where(Message.user_id == user_id)
        if parent_id is not None:
            stmt = stmt.where(Message.parent_id == parent_id)
        return await _paginate(stmt, current, size, Message.id.desc())

    async def get_message_by_id(self, message_id: int) -> Message | None:
        """
        根据 ID 查询留言。

        :param message_id: 留言 ID。
        :return: 留言对象。
        """
        return await db.model_first(select(Message).where(Message.id == message_id))

    async def update_message(self, message: Message, data: dict[str, Any]) -> Message:
        """
        更新留言。

        :param message: 留言对象。
        :param data: 更新数据。
        :return: 留言对象。
        """
        return await _update(message, data)

    async def delete_message(self, message_id: int) -> None:
        """
        删除留言。

        :param message_id: 留言 ID。
        :return: None。
        """
        await _delete(Message, message_id)
