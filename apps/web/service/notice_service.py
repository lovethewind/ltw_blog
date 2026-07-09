import asyncio

from sqlalchemy import delete, func, select, update

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.notice import NoticeTypeEnum
from apps.base.models.notice import Notice
from apps.web.core.context_vars import ContextVars
from apps.web.dto.notice_dto import NoticeDTO
from apps.web.dto.user_dto import UserBaseInfoDTO
from apps.web.utils.ws_util import manager
from apps.web.vo.batch_vo import BatchVO


@Component()
class NoticeService:

    async def get_unread_notice_count(self) -> dict:
        """
        获取各类消息未读数量。

        :return: 各消息类型未读数量。
        """
        user_id = ContextVars.token_user_id.get()
        count_stmt = (
            select(Notice.notice_type, func.count(Notice.id))
            .where(Notice.user_id == user_id, Notice.is_read.is_(False))
            .group_by(Notice.notice_type)
        )
        count_info_list = await db.all(count_stmt)
        count_info_map = dict(count_info_list)
        ret = {
            item.value: count_info_map.get(item.value, 0) for item in NoticeTypeEnum.__dict__["_member_map_"].values()
        }
        return ret

    async def get_notice_list(self, notice_type: NoticeTypeEnum, current: int, size: int) -> dict:
        """
        获取消息列表。

        :param notice_type: 消息类型。
        :param current: 当前页码。
        :param size: 每页数量。
        :return: 消息分页结果。
        """
        user_id = ContextVars.token_user_id.get()
        offset, limit = db.page(current, size)
        count_stmt = (
            select(func.count())
            .select_from(Notice)
            .where(
                Notice.user_id == user_id,
                Notice.notice_type == notice_type,
            )
        )
        notice_stmt = (
            select(Notice)
            .where(Notice.user_id == user_id, Notice.notice_type == notice_type)
            .order_by(Notice.id.desc())
            .offset(offset)
            .limit(limit)
        )
        total, notices = await asyncio.gather(
            db.scalar(count_stmt),
            db.model_all(notice_stmt),
        )
        records = NoticeDTO.bulk_model_validate(notices)
        for item in records:
            if item.notice_type == NoticeTypeEnum.SYSTEM:
                continue
            item.detail.from_user = await manager.get_user_info(item.detail.from_user_id, UserBaseInfoDTO)
        return {"total": total, "records": records}

    async def update(self, batch_vo: BatchVO) -> None:
        """
        更新消息为已读。

        :param batch_vo: 批量操作参数。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        stmt = update(Notice).where(Notice.id.in_(batch_vo.ids), Notice.user_id == user_id).values(is_read=True)
        await db.execute(stmt)

    async def delete(self, batch_vo: BatchVO) -> None:
        """
        删除消息。

        :param batch_vo: 批量操作参数。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        stmt = delete(Notice).where(Notice.id.in_(batch_vo.ids), Notice.user_id == user_id)
        await db.execute(stmt)

    async def clear_notice(self, notice_type: NoticeTypeEnum) -> None:
        """
        清空消息。

        :param notice_type: 消息类型。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        stmt = delete(Notice).where(Notice.user_id == user_id, Notice.notice_type == notice_type)
        await db.execute(stmt)
