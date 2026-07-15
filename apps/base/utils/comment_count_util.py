from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.base.enum.action import ObjectTypeEnum
from apps.base.enum.comment import CommentStatusEnum
from apps.base.models.picture import Picture


async def sync_picture_comment_count(
    session: AsyncSession,
    obj_type: int,
    obj_id: int,
    old_status: int | None,
    new_status: int | None,
) -> None:
    """
    根据图片评论状态变化同步评论数量。

    :param session: 当前数据库事务 Session。
    :param obj_type: 评论对象类型。
    :param obj_id: 评论对象 ID。
    :param old_status: 变更前的评论状态；新增评论时为空。
    :param new_status: 变更后的评论状态；永久删除时为空。
    :return: None。
    """
    if obj_type != ObjectTypeEnum.PICTURE:
        return
    count_delta = int(new_status == CommentStatusEnum.PASS) - int(old_status == CommentStatusEnum.PASS)
    if not count_delta:
        return
    await session.execute(
        update(Picture)
        .where(Picture.id == obj_id)
        .values(comment_count=func.greatest(Picture.comment_count + count_delta, 0))
    )
