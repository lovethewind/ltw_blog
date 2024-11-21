from typing import Iterable

from apps.base.core.depend_inject import Component
from apps.base.models.source import Source


@Component()
class SourceService:

    async def check_and_update_source_status(self, old_urls: str | Iterable[str], new_urls: str | Iterable[str],
                                             user_id: int):
        """
        检查并更新资源为已删除状态
        :param old_urls:
        :param new_urls:
        :param user_id:
        :return:
        """
        if not old_urls or not new_urls or old_urls == new_urls:
            return
        old_urls = set(old_urls)
        new_urls = set(new_urls)
        remove_urls = old_urls - new_urls
        await self._update_source_status(remove_urls, user_id)

    async def change_source_status(self, urls: str | Iterable[str], user_id: int):
        """
        标记资源为已删除状态
        :param urls:
        :param user_id:
        :return:
        """
        if not urls:
            return
        await self._update_source_status(urls, user_id)

    async def _update_source_status(self, url: str | Iterable[str], user_id: int):
        """
        更新资源为已删除状态
        :param url:
        :param user_id:
        :return:
        """
        urls = set(url) if isinstance(url, str) else url
        await Source.filter(user_id=user_id, url__in=urls).update(is_deleted=True)
