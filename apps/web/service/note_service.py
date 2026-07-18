from datetime import datetime, timedelta

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.note import Note, NoteFolder, NoteHistory, NoteTag, NoteTagRelation
from apps.web.core.context_vars import ContextVars
from apps.web.dto.note_dto import NoteDTO, NoteHistoryDTO, NoteHistoryListDTO, NoteListDTO, NoteTagDTO
from apps.web.vo.note_vo import NoteCreateVO, NotePinVO, NoteQueryVO, NoteUpdateVO


@Component()
class NoteService:
    """处理当前用户的私人笔记。"""

    HISTORY_INTERVAL = timedelta(minutes=5)
    HISTORY_LIMIT = 50

    async def list_notes(
        self, current: int, size: int, note_query_vo: NoteQueryVO
    ) -> dict[str, int | list[NoteListDTO]]:
        """
        分页查询当前用户的笔记列表。

        :param current: 当前页码。
        :param size: 每页数量。
        :param note_query_vo: 列表查询参数。
        :return: 包含总数和笔记列表的分页结果。
        """
        user_id = ContextVars.token_user_id.get()
        filters = [Note.user_id == user_id, Note.is_deleted.is_(note_query_vo.is_deleted)]
        if note_query_vo.keyword:
            filters.append(Note.title.icontains(note_query_vo.keyword))
        if note_query_vo.folder_id == 0:
            filters.append(Note.folder_id.is_(None))
        elif note_query_vo.folder_id is not None:
            filters.append(Note.folder_id == note_query_vo.folder_id)
        if note_query_vo.tag_id is not None:
            note_ids = select(NoteTagRelation.note_id).where(NoteTagRelation.tag_id == note_query_vo.tag_id)
            filters.append(Note.id.in_(note_ids))
        if note_query_vo.is_pinned is not None:
            filters.append(Note.is_pinned == note_query_vo.is_pinned)
        offset, limit = db.page(current, size)
        total = await db.scalar(select(func.count()).select_from(Note).where(*filters))
        notes = await db.model_all(
            select(Note)
            .where(*filters)
            .order_by(Note.is_pinned.desc(), Note.update_time.desc(), Note.id.desc())
            .offset(offset)
            .limit(limit)
        )
        tag_map = await self._get_note_tag_map([note.id for note in notes])
        return {
            "total": total,
            "records": [
                NoteListDTO.model_validate(note, from_attributes=True).model_copy(
                    update={"tag_list": tag_map.get(note.id, [])}
                )
                for note in notes
            ],
        }

    async def add(self, note_create_vo: NoteCreateVO) -> int:
        """
        创建当前用户的笔记。

        :param note_create_vo: 笔记创建参数。
        :return: 新建笔记 ID。
        """
        user_id = ContextVars.token_user_id.get()
        if note_create_vo.folder_id is not None:
            await self._ensure_folder_owned(note_create_vo.folder_id)
        tag_ids = await self._ensure_tags_owned(note_create_vo.tag_ids)
        note = Note(
            user_id=user_id,
            title=self._normalize_title(note_create_vo.title),
            content=note_create_vo.content,
            folder_id=note_create_vo.folder_id,
        )
        async with db.atomic() as session:
            session.add(note)
            await session.flush()
            await self._replace_tag_relations(session, note.id, tag_ids)
        return note.id

    async def detail(self, note_id: int) -> NoteDTO:
        """
        查询当前用户的笔记详情。

        :param note_id: 笔记 ID。
        :return: 笔记详情。
        """
        note = await self._get_owned_note(note_id)
        tag_map = await self._get_note_tag_map([note.id])
        return NoteDTO.model_validate(note, from_attributes=True).model_copy(
            update={"tag_list": tag_map.get(note.id, [])}
        )

    async def update(self, note_id: int, note_update_vo: NoteUpdateVO) -> None:
        """
        更新当前用户的笔记及其标签关联。

        :param note_id: 笔记 ID。
        :param note_update_vo: 笔记更新参数。
        :return: None。
        """
        note = await self._get_owned_note(note_id)
        updated_fields = note_update_vo.model_fields_set
        if "folder_id" in updated_fields and note_update_vo.folder_id is not None:
            await self._ensure_folder_owned(note_update_vo.folder_id)
        tag_ids = None
        if "tag_ids" in updated_fields and note_update_vo.tag_ids is not None:
            tag_ids = await self._ensure_tags_owned(note_update_vo.tag_ids)
        current_tag_ids = await self._get_note_tag_ids(note.id)
        next_title = self._normalize_title(note_update_vo.title) if "title" in updated_fields else note.title
        next_content = note_update_vo.content if "content" in updated_fields else note.content
        next_folder_id = note_update_vo.folder_id if "folder_id" in updated_fields else note.folder_id
        next_tag_ids = tag_ids if tag_ids is not None else current_tag_ids
        has_changes = not (
            next_title == note.title
            and next_content == note.content
            and next_folder_id == note.folder_id
            and set(next_tag_ids) == set(current_tag_ids)
        )
        if not has_changes:
            return
        async with db.atomic() as session:
            await self._save_history_snapshot(session, note, current_tag_ids)
            note.title = next_title
            note.content = next_content
            note.folder_id = next_folder_id
            session.add(note)
            if tag_ids is not None:
                await self._replace_tag_relations(session, note.id, tag_ids)
            await session.flush()

    async def list_history(self, note_id: int, current: int, size: int) -> dict[str, int | list[NoteHistoryListDTO]]:
        """
        分页查询当前用户指定笔记的历史版本。

        :param note_id: 笔记 ID。
        :param current: 当前页码。
        :param size: 每页数量。
        :return: 历史版本分页结果。
        """
        note = await self._get_owned_note(note_id)
        offset, limit = db.page(current, min(size, self.HISTORY_LIMIT))
        filters = [NoteHistory.note_id == note.id, NoteHistory.user_id == note.user_id]
        total = await db.scalar(select(func.count()).select_from(NoteHistory).where(*filters))
        histories = await db.model_all(
            select(NoteHistory)
            .where(*filters)
            .order_by(NoteHistory.create_time.desc(), NoteHistory.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return {
            "total": total,
            "records": [
                NoteHistoryListDTO(
                    id=history.id,
                    title=history.title,
                    content_preview=self._history_content_preview(history.content),
                    create_time=history.create_time,
                )
                for history in histories
            ],
        }

    async def history_detail(self, note_id: int, history_id: int) -> NoteHistoryDTO:
        """
        查询当前用户指定笔记的历史版本详情。

        :param note_id: 笔记 ID。
        :param history_id: 历史版本 ID。
        :return: 历史版本详情。
        """
        note = await self._get_owned_note(note_id)
        history = await self._get_owned_history(note.id, history_id, note.user_id)
        return NoteHistoryDTO.model_validate(history, from_attributes=True)

    async def restore_history(self, note_id: int, history_id: int) -> None:
        """
        恢复指定历史版本，并在恢复前强制保留当前版本。

        :param note_id: 笔记 ID。
        :param history_id: 历史版本 ID。
        :return: None。
        """
        note = await self._get_owned_note(note_id)
        history = await self._get_owned_history(note.id, history_id, note.user_id)
        current_tag_ids = await self._get_note_tag_ids(note.id)
        folder_id = await self._resolve_history_folder_id(history.folder_id)
        tag_ids = await self._filter_owned_tag_ids(history.tag_ids)
        async with db.atomic() as session:
            await self._save_history_snapshot(
                session,
                note,
                current_tag_ids,
                force=True,
            )
            note.title = history.title
            note.content = history.content
            note.folder_id = folder_id
            session.add(note)
            await self._replace_tag_relations(session, note.id, tag_ids)
            await session.flush()

    async def delete_history(self, note_id: int, history_id: int) -> None:
        """
        删除当前用户指定笔记的单个历史版本。

        :param note_id: 笔记 ID。
        :param history_id: 历史版本 ID。
        :return: None。
        """
        note = await self._get_owned_note(note_id)
        history = await self._get_owned_history(note.id, history_id, note.user_id)
        async with db.atomic() as session:
            await session.delete(history)
            await session.flush()

    async def set_pinned(self, note_id: int, note_pin_vo: NotePinVO) -> None:
        """
        设置当前用户笔记的置顶状态。

        :param note_id: 笔记 ID。
        :param note_pin_vo: 置顶状态参数。
        :return: None。
        """
        note = await self._get_owned_note(note_id)
        note.is_pinned = note_pin_vo.is_pinned
        async with db.atomic() as session:
            session.add(note)
            await session.flush()

    async def remove(self, note_id: int) -> None:
        """
        将当前用户的笔记移入回收站。

        :param note_id: 笔记 ID。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        async with db.atomic() as session:
            result = await session.execute(
                update(Note)
                .where(Note.id == note_id, Note.user_id == user_id, Note.is_deleted.is_(False))
                .values(is_deleted=True, deleted_time=datetime.now())
            )
            if result.rowcount == 0:
                raise MyException(ErrorCode.DATA_NOT_EXISTS)

    async def restore(self, note_id: int) -> None:
        """
        恢复当前用户回收站中的笔记。

        :param note_id: 笔记 ID。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        async with db.atomic() as session:
            result = await session.execute(
                update(Note)
                .where(Note.id == note_id, Note.user_id == user_id, Note.is_deleted.is_(True))
                .values(is_deleted=False, deleted_time=None)
            )
            if result.rowcount == 0:
                raise MyException(ErrorCode.DATA_NOT_EXISTS)

    async def permanent_delete(self, note_id: int) -> None:
        """
        永久删除当前用户回收站中的笔记。

        :param note_id: 笔记 ID。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        async with db.atomic() as session:
            result = await session.execute(
                delete(Note).where(Note.id == note_id, Note.user_id == user_id, Note.is_deleted.is_(True))
            )
            if result.rowcount == 0:
                raise MyException(ErrorCode.DATA_NOT_EXISTS)

    async def _get_owned_note(self, note_id: int, is_deleted: bool | None = None) -> Note:
        """
        获取属于当前用户的笔记，不存在时抛出异常。

        :param note_id: 笔记 ID。
        :param is_deleted: 可选的回收站状态。
        :return: 当前用户的笔记。
        """
        user_id = ContextVars.token_user_id.get()
        filters = [Note.id == note_id, Note.user_id == user_id]
        if is_deleted is not None:
            filters.append(Note.is_deleted.is_(is_deleted))
        note = await db.model_first(select(Note).where(*filters))
        if not note:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return note

    async def _get_owned_history(self, note_id: int, history_id: int, user_id: int) -> NoteHistory:
        """
        获取属于当前用户和笔记的历史版本。

        :param note_id: 笔记 ID。
        :param history_id: 历史版本 ID。
        :param user_id: 当前用户 ID。
        :return: 历史版本模型。
        """
        history = await db.model_first(
            select(NoteHistory).where(
                NoteHistory.id == history_id,
                NoteHistory.note_id == note_id,
                NoteHistory.user_id == user_id,
            )
        )
        if not history:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return history

    async def _save_history_snapshot(
        self,
        session: AsyncSession,
        note: Note,
        tag_ids: list[int],
        force: bool = False,
    ) -> None:
        """
        在当前事务中保存笔记快照，并按时间窗口更新最近快照及清理旧版本。

        :param session: 当前数据库事务 Session。
        :param note: 更新前的笔记。
        :param tag_ids: 更新前的标签 ID 列表。
        :param force: 是否忽略时间窗口强制保存。
        :return: None。
        """
        if not force:
            latest = await session.scalar(
                select(NoteHistory)
                .where(NoteHistory.note_id == note.id, NoteHistory.user_id == note.user_id)
                .order_by(NoteHistory.create_time.desc(), NoteHistory.id.desc())
                .limit(1)
            )
            if latest and datetime.now() - latest.create_time < self.HISTORY_INTERVAL:
                latest.title = note.title
                latest.content = note.content
                latest.folder_id = note.folder_id
                latest.tag_ids = list(tag_ids)
                return
        session.add(
            NoteHistory(
                note_id=note.id,
                user_id=note.user_id,
                title=note.title,
                content=note.content,
                folder_id=note.folder_id,
                tag_ids=list(tag_ids),
            )
        )
        await session.flush()
        old_ids = (
            await session.scalars(
                select(NoteHistory.id)
                .where(NoteHistory.note_id == note.id, NoteHistory.user_id == note.user_id)
                .order_by(NoteHistory.create_time.desc(), NoteHistory.id.desc())
                .offset(self.HISTORY_LIMIT)
            )
        ).all()
        if old_ids:
            await session.execute(delete(NoteHistory).where(NoteHistory.id.in_(old_ids)))

    async def _get_note_tag_ids(self, note_id: int) -> list[int]:
        """
        查询笔记当前关联的标签 ID。

        :param note_id: 笔记 ID。
        :return: 标签 ID 列表。
        """
        return list(
            await db.model_all(
                select(NoteTagRelation.tag_id).where(NoteTagRelation.note_id == note_id).order_by(NoteTagRelation.id)
            )
        )

    async def _resolve_history_folder_id(self, folder_id: int | None) -> int | None:
        """
        解析历史版本中仍可使用的文件夹 ID。

        :param folder_id: 历史文件夹 ID。
        :return: 有效文件夹 ID；不存在或已删除时返回 None。
        """
        if folder_id is None:
            return None
        user_id = ContextVars.token_user_id.get()
        folder = await db.model_first(
            select(NoteFolder).where(
                NoteFolder.id == folder_id,
                NoteFolder.user_id == user_id,
                NoteFolder.is_deleted.is_(False),
            )
        )
        return folder.id if folder else None

    async def _filter_owned_tag_ids(self, tag_ids: list[int]) -> list[int]:
        """
        过滤历史版本中已失效或不属于当前用户的标签 ID。

        :param tag_ids: 历史标签 ID 列表。
        :return: 仍然有效的标签 ID 列表。
        """
        if not tag_ids:
            return []
        user_id = ContextVars.token_user_id.get()
        valid_ids = set(
            await db.model_all(select(NoteTag.id).where(NoteTag.id.in_(tag_ids), NoteTag.user_id == user_id))
        )
        return [tag_id for tag_id in tag_ids if tag_id in valid_ids]

    async def _ensure_folder_owned(self, folder_id: int) -> None:
        """
        验证文件夹属于当前用户。

        :param folder_id: 文件夹 ID。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        folder = await db.model_first(
            select(NoteFolder).where(NoteFolder.id == folder_id, NoteFolder.user_id == user_id)
        )
        if not folder:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)

    async def _ensure_tags_owned(self, tag_ids: list[int]) -> list[int]:
        """
        验证全部标签属于当前用户，并去除重复标签。

        :param tag_ids: 待验证标签 ID。
        :return: 去重后的标签 ID 列表。
        """
        user_id = ContextVars.token_user_id.get()
        unique_tag_ids = list(dict.fromkeys(tag_ids))
        if not unique_tag_ids:
            return []
        tags = await db.model_all(select(NoteTag).where(NoteTag.id.in_(unique_tag_ids), NoteTag.user_id == user_id))
        if len(tags) != len(unique_tag_ids):
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return unique_tag_ids

    async def _replace_tag_relations(self, session: AsyncSession, note_id: int, tag_ids: list[int]) -> None:
        """
        在当前事务中替换笔记全部标签关联。

        :param session: 当前数据库事务 Session。
        :param note_id: 笔记 ID。
        :param tag_ids: 已完成归属校验的标签 ID 列表。
        :return: None。
        """
        await session.execute(delete(NoteTagRelation).where(NoteTagRelation.note_id == note_id))
        for tag_id in tag_ids:
            await session.execute(insert(NoteTagRelation).values(note_id=note_id, tag_id=tag_id))

    async def _get_note_tag_map(self, note_ids: list[int]) -> dict[int, list[NoteTagDTO]]:
        """
        查询当前用户笔记的标签，并按笔记 ID 分组。

        :param note_ids: 笔记 ID 列表。
        :return: 笔记 ID 到标签 DTO 列表的映射。
        """
        if not note_ids:
            return {}
        user_id = ContextVars.token_user_id.get()
        rows = await db.all(
            select(NoteTagRelation.note_id, NoteTag)
            .join(NoteTag, NoteTag.id == NoteTagRelation.tag_id)
            .join(Note, Note.id == NoteTagRelation.note_id)
            .where(
                NoteTagRelation.note_id.in_(note_ids),
                Note.user_id == user_id,
                NoteTag.user_id == user_id,
            )
            .order_by(NoteTag.id.desc())
        )
        tag_map: dict[int, list[NoteTagDTO]] = {}
        for note_id, tag in rows:
            tag_map.setdefault(note_id, []).append(NoteTagDTO.model_validate(tag, from_attributes=True))
        return tag_map

    @staticmethod
    def _normalize_title(title: str | None) -> str:
        """
        将空白标题归一化为默认标题。

        :param title: 原始标题。
        :return: 可持久化的标题。
        """
        normalized_title = (title or "").strip()
        return normalized_title or "无标题笔记"

    @staticmethod
    def _history_content_preview(content: str) -> str:
        """
        生成历史版本列表使用的单行正文摘要。

        :param content: Markdown 正文。
        :return: 最长 120 个字符的单行摘要。
        """
        return " ".join(content.split())[:120]
