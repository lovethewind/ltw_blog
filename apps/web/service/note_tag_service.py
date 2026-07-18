from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.note import Note, NoteTag, NoteTagRelation
from apps.web.core.context_vars import ContextVars
from apps.web.dto.note_dto import NoteTagDTO
from apps.web.vo.note_tag_vo import NoteTagVO


@Component()
class NoteTagService:
    """处理当前用户的笔记标签。"""

    async def list(self) -> list[NoteTagDTO]:
        """
        查询当前用户的标签列表。

        :return: 标签 DTO 列表。
        """
        user_id = ContextVars.token_user_id.get()
        tags = await db.model_all(select(NoteTag).where(NoteTag.user_id == user_id).order_by(NoteTag.id.asc()))
        return [NoteTagDTO.model_validate(tag, from_attributes=True) for tag in tags]

    async def add(self, note_tag_vo: NoteTagVO) -> NoteTagDTO:
        """
        为当前用户新增标签。

        :param note_tag_vo: 标签名称参数。
        :return: 新建标签 DTO。
        :raises MyException: 名称不合法或已重复时抛出。
        """
        user_id = ContextVars.token_user_id.get()
        name = self._normalize_name(note_tag_vo.name)
        tag = NoteTag(user_id=user_id, name=name)
        try:
            async with db.atomic() as session:
                session.add(tag)
                await session.flush()
        except IntegrityError as exc:
            raise MyException.param_err("标签名称已存在") from exc
        return NoteTagDTO.model_validate(tag, from_attributes=True)

    async def rename(self, tag_id: int, note_tag_vo: NoteTagVO) -> None:
        """
        重命名当前用户的标签。

        :param tag_id: 标签 ID。
        :param note_tag_vo: 新名称参数。
        :return: None。
        :raises MyException: 标签不存在、无归属或名称重复时抛出。
        """
        user_id = ContextVars.token_user_id.get()
        name = self._normalize_name(note_tag_vo.name)
        try:
            async with db.atomic() as session:
                result = await session.execute(
                    update(NoteTag).where(NoteTag.id == tag_id, NoteTag.user_id == user_id).values(name=name)
                )
                if result.rowcount != 1:
                    raise MyException(ErrorCode.DATA_NOT_EXISTS)
        except IntegrityError as exc:
            raise MyException.param_err("标签名称已存在") from exc

    async def delete(self, tag_id: int) -> None:
        """
        删除当前用户标签及其本人笔记的关联。

        :param tag_id: 标签 ID。
        :return: None。
        :raises MyException: 标签不存在或无归属时抛出。
        """
        user_id = ContextVars.token_user_id.get()
        owned_notes = select(Note.id).where(Note.user_id == user_id)
        owned_tag = select(NoteTag.id).where(NoteTag.id == tag_id, NoteTag.user_id == user_id)
        foreign_relation_exists = (
            select(NoteTagRelation.id)
            .join(Note, Note.id == NoteTagRelation.note_id)
            .where(NoteTagRelation.tag_id == tag_id, Note.user_id != user_id)
            .exists()
        )
        async with db.atomic() as session:
            await session.execute(
                delete(NoteTagRelation).where(
                    NoteTagRelation.tag_id == tag_id,
                    NoteTagRelation.note_id.in_(owned_notes),
                    NoteTagRelation.tag_id.in_(owned_tag),
                )
            )
            result = await session.execute(
                delete(NoteTag).where(
                    NoteTag.id == tag_id,
                    NoteTag.user_id == user_id,
                    ~foreign_relation_exists,
                )
            )
            if result.rowcount != 1:
                raise MyException(ErrorCode.DATA_NOT_EXISTS)

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        规范化标签名称并校验长度。

        :param name: 原始名称。
        :return: 去除首尾空白后的名称。
        :raises MyException: 名称为空或超过最大长度时抛出。
        """
        normalized_name = name.strip()
        if not normalized_name:
            raise MyException.param_err("标签名称不能为空")
        if len(normalized_name) > 50:
            raise MyException.param_err("标签名称不能超过 50 个字符")
        return normalized_name
