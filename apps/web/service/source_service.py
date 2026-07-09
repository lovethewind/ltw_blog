from typing import Iterable

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.source import Source


@Component()
class SourceService:

    async def check_and_update_source_status(
        self,
        old_urls: str | Iterable[str],
        new_urls: str | Iterable[str],
        user_id: int,
        session: AsyncSession | None = None,
    ) -> None:
        """
        检查并更新资源为已删除状态

        :param old_urls: 旧资源 URL 或资源 URL 列表。
        :param new_urls: 新资源 URL 或资源 URL 列表。
        :param user_id: 用户 ID。
        :param session: 可复用的数据库会话。
        :return: None。
        """
        if not old_urls or not new_urls or old_urls == new_urls:
            return
        old_urls = set(old_urls)
        new_urls = set(new_urls)
        remove_urls = old_urls - new_urls
        await self._update_source_status(remove_urls, user_id, session=session)

    async def change_source_status(
        self, urls: str | Iterable[str], user_id: int, session: AsyncSession | None = None
    ) -> None:
        """
        标记资源为已删除状态

        :param urls: 资源 URL 或资源 URL 列表。
        :param user_id: 用户 ID。
        :param session: 可复用的数据库会话。
        :return: None。
        """
        if not urls:
            return
        await self._update_source_status(urls, user_id, session=session)

    async def _update_source_status(
        self, url: str | Iterable[str], user_id: int, session: AsyncSession | None = None
    ) -> None:
        """
        更新资源为已删除状态

        :param url: 资源 URL 或资源 URL 列表。
        :param user_id: 用户 ID。
        :param session: 可复用的数据库会话。
        :return: None。
        """
        urls = {url} if isinstance(url, str) else set(url)
        if not urls:
            return
        stmt = update(Source).where(Source.user_id == user_id, Source.url.in_(urls)).values(is_deleted=True)
        if session:
            await session.execute(stmt)
        else:
            await db.execute(stmt)
