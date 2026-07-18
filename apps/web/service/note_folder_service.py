from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.note import Note, NoteFolder
from apps.web.core.context_vars import ContextVars
from apps.web.dto.note_dto import NoteFolderDTO
from apps.web.vo.note_folder_vo import NoteFolderSortVO, NoteFolderVO


@Component()
class NoteFolderService:
    """处理当前用户的笔记文件夹。"""

    async def list(self, is_deleted: bool = False) -> list[NoteFolderDTO]:
        """
        查询当前用户的文件夹列表。

        :return: 文件夹 DTO 列表。
        """
        user_id = ContextVars.token_user_id.get()
        folders = await db.model_all(
            select(NoteFolder)
            .where(NoteFolder.user_id == user_id, NoteFolder.is_deleted == is_deleted)
            .order_by(NoteFolder.sort_order.asc(), NoteFolder.id.asc())
        )
        return [NoteFolderDTO.model_validate(folder, from_attributes=True) for folder in folders]

    async def add(self, note_folder_vo: NoteFolderVO) -> NoteFolderDTO:
        """
        为当前用户新增文件夹。

        :param note_folder_vo: 文件夹名称参数。
        :return: 新建文件夹 DTO。
        :raises MyException: 名称不合法或已重复时抛出。
        """
        user_id = ContextVars.token_user_id.get()
        name = self._normalize_name(note_folder_vo.name)
        parent_id = note_folder_vo.parent_id
        if parent_id is not None:
            parent = await db.model_first(
                select(NoteFolder).where(
                    NoteFolder.id == parent_id,
                    NoteFolder.user_id == user_id,
                    NoteFolder.is_deleted.is_(False),
                )
            )
            if parent is None:
                raise MyException(ErrorCode.DATA_NOT_EXISTS)
        folder = NoteFolder(user_id=user_id, parent_id=parent_id, name=name, sort_order=0, is_deleted=False)
        try:
            async with db.atomic() as session:
                session.add(folder)
                await session.flush()
        except IntegrityError as exc:
            raise MyException.param_err("文件夹名称已存在") from exc
        return NoteFolderDTO.model_validate(folder, from_attributes=True)

    async def update_sort(self, note_folder_sort_vo: NoteFolderSortVO) -> None:
        """
        按传入顺序更新当前用户全部文件夹的排序值。

        :param note_folder_sort_vo: 文件夹排序参数。
        :return: None。
        :raises MyException: ID 集合存在重复、越权或并发变更时抛出。
        """
        user_id = ContextVars.token_user_id.get()
        folder_ids = note_folder_sort_vo.folder_ids
        if len(set(folder_ids)) != len(folder_ids):
            raise MyException.param_err("文件夹排序 ID 不允许重复")
        folders = await db.model_all(
            select(NoteFolder).where(NoteFolder.id.in_(folder_ids), NoteFolder.user_id == user_id)
        )
        if len(folders) != len(folder_ids):
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        async with db.atomic() as session:
            for sort_order, folder_id in enumerate(folder_ids):
                result = await session.execute(
                    update(NoteFolder)
                    .where(NoteFolder.id == folder_id, NoteFolder.user_id == user_id)
                    .values(sort_order=sort_order)
                )
                if result.rowcount != 1:
                    raise MyException(ErrorCode.DATA_NOT_EXISTS)

    async def rename(self, folder_id: int, note_folder_vo: NoteFolderVO) -> None:
        """
        重命名当前用户的文件夹。

        :param folder_id: 文件夹 ID。
        :param note_folder_vo: 新名称参数。
        :return: None。
        :raises MyException: 文件夹不存在、无归属或名称重复时抛出。
        """
        user_id = ContextVars.token_user_id.get()
        name = self._normalize_name(note_folder_vo.name)
        try:
            async with db.atomic() as session:
                result = await session.execute(
                    update(NoteFolder)
                    .where(NoteFolder.id == folder_id, NoteFolder.user_id == user_id)
                    .values(name=name)
                )
                if result.rowcount != 1:
                    raise MyException(ErrorCode.DATA_NOT_EXISTS)
        except IntegrityError as exc:
            raise MyException.param_err("文件夹名称已存在") from exc

    async def delete(self, folder_id: int) -> None:
        """
        将当前用户文件夹子树及其中未删除笔记整体移入回收站。

        :param folder_id: 文件夹 ID。
        :return: None。
        :raises MyException: 文件夹不存在或无归属时抛出。
        """
        user_id = ContextVars.token_user_id.get()
        folders = await db.model_all(select(NoteFolder).where(NoteFolder.user_id == user_id))
        folder_ids = self._collect_subtree_ids(folders, folder_id, deleted=False)
        if not folder_ids:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        deleted_time = datetime.now()
        async with db.atomic() as session:
            result = await session.execute(
                update(NoteFolder)
                .where(
                    NoteFolder.id.in_(folder_ids),
                    NoteFolder.user_id == user_id,
                    NoteFolder.is_deleted.is_(False),
                )
                .values(is_deleted=True, deleted_time=deleted_time, deleted_root_id=folder_id)
            )
            if result.rowcount != len(folder_ids):
                raise MyException(ErrorCode.DATA_NOT_EXISTS)
            await session.execute(
                update(Note)
                .where(
                    Note.folder_id.in_(folder_ids),
                    Note.user_id == user_id,
                    Note.is_deleted.is_(False),
                )
                .values(is_deleted=True, deleted_time=deleted_time, deleted_by_folder_id=folder_id)
            )

    async def restore(self, folder_id: int) -> None:
        """
        恢复由同一次删除操作移入回收站的文件夹子树和笔记。

        :param folder_id: 删除操作的根文件夹 ID。
        :return: None。
        :raises MyException: 根文件夹不存在或不属于当前用户时抛出。
        """
        user_id = ContextVars.token_user_id.get()
        folders = await db.model_all(select(NoteFolder).where(NoteFolder.user_id == user_id))
        folder_ids = [folder.id for folder in folders if folder.is_deleted and folder.deleted_root_id == folder_id]
        if folder_id not in folder_ids:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        async with db.atomic() as session:
            result = await session.execute(
                update(NoteFolder)
                .where(NoteFolder.id.in_(folder_ids), NoteFolder.user_id == user_id)
                .values(is_deleted=False, deleted_time=None, deleted_root_id=None)
            )
            if result.rowcount != len(folder_ids):
                raise MyException(ErrorCode.DATA_NOT_EXISTS)
            await session.execute(
                update(Note)
                .where(Note.user_id == user_id, Note.deleted_by_folder_id == folder_id)
                .values(is_deleted=False, deleted_time=None, deleted_by_folder_id=None)
            )

    async def permanent_delete(self, folder_id: int) -> None:
        """
        永久删除回收站中的文件夹子树及随其删除的笔记。

        :param folder_id: 删除操作的根文件夹 ID。
        :return: None。
        :raises MyException: 根文件夹不存在或不属于当前用户时抛出。
        """
        user_id = ContextVars.token_user_id.get()
        folders = await db.model_all(select(NoteFolder).where(NoteFolder.user_id == user_id))
        folder_ids = [folder.id for folder in folders if folder.is_deleted and folder.deleted_root_id == folder_id]
        if folder_id not in folder_ids:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        async with db.atomic() as session:
            await session.execute(delete(Note).where(Note.user_id == user_id, Note.deleted_by_folder_id == folder_id))
            await session.execute(
                update(Note).where(Note.user_id == user_id, Note.folder_id.in_(folder_ids)).values(folder_id=None)
            )
            result = await session.execute(
                delete(NoteFolder).where(NoteFolder.id.in_(folder_ids), NoteFolder.user_id == user_id)
            )
            if result.rowcount != len(folder_ids):
                raise MyException(ErrorCode.DATA_NOT_EXISTS)

    @staticmethod
    def _collect_subtree_ids(folders: list[NoteFolder], root_id: int, deleted: bool) -> list[int]:
        """
        按父子关系收集指定状态的文件夹子树 ID。

        :param folders: 当前用户的全部文件夹。
        :param root_id: 子树根文件夹 ID。
        :param deleted: 是否收集回收站文件夹。
        :return: 从根节点开始的文件夹 ID 列表。
        """
        folder_map = {folder.id: folder for folder in folders if folder.is_deleted is deleted}
        if root_id not in folder_map:
            return []
        children_map: dict[int, list[int]] = {}
        for folder in folder_map.values():
            if folder.parent_id is not None:
                children_map.setdefault(folder.parent_id, []).append(folder.id)
        result: list[int] = []
        pending = [root_id]
        while pending:
            current_id = pending.pop()
            result.append(current_id)
            pending.extend(reversed(children_map.get(current_id, [])))
        return result

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        规范化文件夹名称并校验长度。

        :param name: 原始名称。
        :return: 去除首尾空白后的名称。
        :raises MyException: 名称为空或超过最大长度时抛出。
        """
        normalized_name = name.strip()
        if not normalized_name:
            raise MyException.param_err("文件夹名称不能为空")
        if len(normalized_name) > 50:
            raise MyException.param_err("文件夹名称不能超过 50 个字符")
        return normalized_name
