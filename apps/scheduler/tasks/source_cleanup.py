from sqlalchemy import delete, select

from apps.base.core.depend_inject import Autowired, Component, GetBean, logger
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.source import Source
from apps.base.utils.oss_util import OssUtil


@Component()
class SourceCleanupTask:
    """已删除资源清理任务。"""

    oss_util: OssUtil = Autowired()

    async def execute(self, batch_size: int = 500) -> int:
        """
        删除已标记资源对应的 OSS 文件和数据库记录。

        单条资源清理失败时保留数据库记录，供下次任务重试。

        :param batch_size: 单次最多清理数量。
        :return: 成功清理的资源数量。
        """
        sources = await db.model_all(
            select(Source).where(Source.is_deleted.is_(True)).order_by(Source.id).limit(batch_size)
        )
        cleaned_count = 0
        for source in sources:
            try:
                await self.oss_util.delete_file(source.url)
                result = await db.execute(delete(Source).where(Source.id == source.id, Source.is_deleted.is_(True)))
                cleaned_count += int(result.rowcount or 0)
            except Exception as exc:
                logger.exception(f"清理资源[{source.id}]失败，将在下次任务重试: {exc}")
        logger.info(f"已删除资源清理完成，共清理 {cleaned_count} 条")
        return cleaned_count


async def cleanup_deleted_sources(batch_size: int = 500) -> int:
    """
    清理已标记删除的 OSS 资源。

    :param batch_size: 单次最多清理数量。
    :return: 成功清理的资源数量。
    """
    task = GetBean(SourceCleanupTask)
    return await task.execute(batch_size)
