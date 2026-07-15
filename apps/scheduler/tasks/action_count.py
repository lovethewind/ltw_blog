from sqlalchemy import select, update

from apps.base.constant.redis_constant import RedisConstant
from apps.base.core.depend_inject import Autowired, Component, GetBean, logger
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.action import ActionTypeEnum, ObjectTypeEnum
from apps.base.models.action import ActionCount
from apps.base.models.picture import Picture
from apps.base.utils.action_count_util import ActionCountDirtyItem, parse_action_count_dirty_member
from apps.base.utils.redis_util import RedisUtil


@Component()
class ActionCountSyncTask:
    """行为计数同步任务。"""

    redis_util: RedisUtil = Autowired()

    async def execute(self, batch_size: int = 500) -> int:
        """
        将 Redis dirty 计数同步到行为统计表。

        :param batch_size: 单次最多同步数量。
        :return: 成功同步的计数项数量。
        """
        redis = self.redis_util.redis
        members = await redis.smembers(RedisConstant.ACTION_COUNT_DIRTY_SET_KEY)
        synced_count = 0
        for member in list(members)[:batch_size]:
            dirty_item = parse_action_count_dirty_member(str(member))
            if not dirty_item:
                await redis.srem(RedisConstant.ACTION_COUNT_DIRTY_SET_KEY, member)
                continue
            count = await redis.hget(dirty_item.redis_hash_key, str(dirty_item.obj_id))
            if count is None:
                await redis.srem(RedisConstant.ACTION_COUNT_DIRTY_SET_KEY, member)
                continue
            await self._save_action_count(dirty_item, int(count))
            await self._remove_synced_dirty_member(dirty_item, str(count), str(member))
            synced_count += 1
        if synced_count:
            logger.info(f"同步行为计数完成，共同步 {synced_count} 条")
        return synced_count

    async def _save_action_count(self, dirty_item: ActionCountDirtyItem, count: int) -> None:
        """
        保存单个行为统计计数。

        :param dirty_item: dirty 计数项。
        :param count: 当前 Redis 计数值。
        :return: None。
        """
        count = max(count, 0)
        action_count = await db.model_first(
            select(ActionCount).where(
                ActionCount.obj_id == dirty_item.obj_id,
                ActionCount.obj_type == dirty_item.obj_type,
                ActionCount.action_type == dirty_item.action_type,
            )
        )
        if action_count:
            action_count.count = count
        else:
            action_count = ActionCount(
                obj_id=dirty_item.obj_id,
                obj_type=dirty_item.obj_type,
                action_type=dirty_item.action_type,
                count=count,
            )
        async with db.atomic() as session:
            session.add(action_count)
            if dirty_item.obj_type == ObjectTypeEnum.PICTURE and dirty_item.action_type == ActionTypeEnum.LIKE:
                await session.execute(update(Picture).where(Picture.id == dirty_item.obj_id).values(like_count=count))
            await session.flush()

    async def _remove_synced_dirty_member(
        self,
        dirty_item: ActionCountDirtyItem,
        expected_count: str,
        member: str,
    ) -> None:
        """
        当 Redis 计数未变化时移除 dirty 标记。

        :param dirty_item: dirty 计数项。
        :param expected_count: 已同步的 Redis 计数值。
        :param member: dirty 集合成员。
        :return: None。
        """
        await self.redis_util.redis.eval(
            """
            if redis.call("HGET", KEYS[1], ARGV[1]) == ARGV[2] then
                return redis.call("SREM", KEYS[2], ARGV[3])
            end
            return 0
            """,
            2,
            dirty_item.redis_hash_key,
            RedisConstant.ACTION_COUNT_DIRTY_SET_KEY,
            str(dirty_item.obj_id),
            expected_count,
            member,
        )


async def sync_action_count(batch_size: int = 500) -> int:
    """
    同步 Redis 行为计数到数据库。

    :param batch_size: 单次最多同步数量。
    :return: 成功同步的计数项数量。
    """
    task = GetBean(ActionCountSyncTask)
    return await task.execute(batch_size)
