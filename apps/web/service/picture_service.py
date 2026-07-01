# @Time    : 2024/9/3 14:05
# @Author  : frank
# @File    : picture_service.py
import asyncio
from typing import Optional

from tortoise.expressions import Q
from tortoise.queryset import QuerySet
from tortoise.transactions import in_transaction

from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.action import ObjectTypeEnum
from apps.base.enum.common import CheckStatusEnum
from apps.base.enum.error_code import ErrorCode
from apps.base.enum.picture import AlbumTypeEnum
from apps.base.exception.my_exception import MyException
from apps.base.models.picture import Picture, PictureAlbum
from apps.base.utils.picture_util import PictureUtil
from apps.base.utils.redis_util import RedisUtil
from apps.web.core.context_vars import ContextVars
from apps.web.dao.comment_dao import CommentDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.picture_dto import PictureAlbumDTO, PictureDTO
from apps.web.dto.user_dto import UserBaseInfoDTO
from apps.web.service.source_service import SourceService
from apps.web.utils.ws_util import manager
from apps.web.vo.batch_vo import BatchVO
from apps.web.vo.picture_vo import (
    PictureAddVO,
    PictureAlbumAddVO,
    PictureAlbumUpdateVO,
    PictureQueryVO,
    PictureUpdateVO,
)


@Component()
class PictureService:
    DEFAULT_PICTURE_ORDERING = ["-id"]
    PICTURE_ORDERING_MAP = {
        "latest": ["-create_time", "-id"],
        "resolution": ["-width", "-height", "-id"],
    }
    PICTURE_METRIC_SORT_TYPES = {"like", "comment"}

    user_dao: UserDao = Autowired()
    comment_dao: CommentDao = Autowired()
    picture_util: PictureUtil = Autowired()
    redis_util: RedisUtil = Autowired()
    source_service: SourceService = Autowired()

    @classmethod
    def _resolve_picture_ordering(cls, picture_query_vo: PictureQueryVO) -> list[str]:
        """
        根据图片查询参数解析数据库排序字段。

        :param picture_query_vo: 图片查询参数。
        :return: 数据库排序字段列表。
        """
        sort_type: Optional[str] = picture_query_vo.sort_type
        if not sort_type:
            return cls.DEFAULT_PICTURE_ORDERING
        return cls.PICTURE_ORDERING_MAP.get(sort_type, cls.DEFAULT_PICTURE_ORDERING)

    @classmethod
    def _is_picture_metric_sort(cls, sort_type: Optional[str]) -> bool:
        """
        判断图片排序类型是否需要按聚合指标排序。

        :param sort_type: 图片排序类型。
        :return: 是否需要按聚合指标排序。
        """
        return sort_type in cls.PICTURE_METRIC_SORT_TYPES

    async def list_album(self, current: int, size: int, is_user: bool = False) -> dict:
        """
        获取图库列表
        :param current:
        :param size:
        :param is_user: 是否查询某个用户
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        if is_user and user_id:
            q = PictureAlbum.filter(~Q(status=CheckStatusEnum.REJECT), user_id=user_id)
        else:
            q = PictureAlbum.filter(album_type=AlbumTypeEnum.PUBLIC, status=CheckStatusEnum.PASS)
        total, albums = await asyncio.gather(
            q.count(),
            q.page(current, size).all(),
        )
        return {"total": total, "records": PictureAlbumDTO.bulk_model_validate(albums)}

    async def add_album(self, picture_album_add_vo: PictureAlbumAddVO):
        """
        添加图库分类
        :param picture_album_add_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        picture_album = PictureAlbum(**picture_album_add_vo.model_dump(exclude_none=True))
        picture_album.user_id = user_id
        picture_album.status = CheckStatusEnum.PASS  # 目前无需审核
        if not picture_album.cover:
            picture_album.cover = await self.picture_util.get_random_img_url()
        await picture_album.save()

    async def update_album(self, picture_album_update_vo: PictureAlbumUpdateVO):
        """
        更新图库分类
        :param picture_album_update_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        picture_album = await PictureAlbum.filter(
            ~Q(status=CheckStatusEnum.REJECT), id=picture_album_update_vo.id, user_id=user_id
        ).first()
        if not picture_album:
            raise MyException(ErrorCode.PICTURE_ALBUM_NOT_EXIST)
        if (
            picture_album.album_type == AlbumTypeEnum.PUBLIC
            and picture_album_update_vo.album_type == AlbumTypeEnum.PRIVATE
        ):
            # 无法公开转私密
            raise MyException(ErrorCode.PICTURE_ALBUM_IS_PUBLIC)
        update_dict = picture_album_update_vo.model_dump(exclude_none=True)
        old_cover_urls = {picture_album.cover}
        new_cover_urls = {update_dict.get("cover", picture_album.cover)}
        await self.source_service.check_and_update_source_status(old_cover_urls, new_cover_urls, user_id)
        await picture_album.update_from_dict(update_dict)
        await picture_album.save(update_fields=update_dict.keys())

    async def delete_album(self, album_id: int):
        """
        删除图库分类
        :param album_id:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        album = await PictureAlbum.filter(
            ~Q(status=CheckStatusEnum.REJECT), album_type=AlbumTypeEnum.PRIVATE, id=album_id, user_id=user_id
        ).first()
        if not album:
            raise MyException(ErrorCode.PICTURE_ALBUM_NOT_EXIST)
        q = Picture.filter(album_id=album_id)
        pictures = await q.all()
        urls = [album.cover]
        picture_ids = []
        for picture in pictures:
            urls.append(picture.url)
            urls.append(picture.thumb_url)
            picture_ids.append(picture.id)
        async with in_transaction():
            # 删除图库下的图片和评论
            await album.delete()
            await self.source_service.change_source_status(urls, user_id)
            await self.comment_dao.clear_comment(picture_ids, obj_type=ObjectTypeEnum.PICTURE)
            await q.delete()

    async def list_picture(
        self, current: int, size: int, picture_query_vo: PictureQueryVO, is_user: bool = False
    ) -> dict:
        """
        查询图片列表
        :param current:
        :param size:
        :param picture_query_vo:
        :param is_user: 是否查询某个用户
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        qa = PictureAlbum
        if is_user and user_id:
            qa = qa.filter(user_id=user_id, status=CheckStatusEnum.PASS)
        else:
            qa = qa.filter(album_type=AlbumTypeEnum.PUBLIC, status=CheckStatusEnum.PASS)
        if picture_query_vo.album_id:
            qa = qa.filter(id=picture_query_vo.album_id)
        album_ids = await qa.values_list("id", flat=True)
        qp = Picture.filter(album_id__in=album_ids, status=CheckStatusEnum.PASS)
        if self._is_picture_metric_sort(picture_query_vo.sort_type):
            total, pictures, picture_comment_count_map = await self._list_metric_sorted_pictures(
                qp, current, size, picture_query_vo.sort_type
            )
        else:
            total, pictures = await asyncio.gather(
                qp.count(),
                qp.order_by(*self._resolve_picture_ordering(picture_query_vo)).page(current, size).all(),
            )
            picture_comment_count_map = None
        records = await self._build_picture_records(pictures, user_id, picture_comment_count_map)
        return {"total": total, "records": records}

    async def _list_metric_sorted_pictures(
        self, qp: QuerySet[Picture], current: int, size: int, sort_type: str
    ) -> tuple[int, list[Picture], dict[int, int] | None]:
        """
        按点赞数或评论数对匹配图片做服务端排序并分页。

        :param qp: 图片查询集。
        :param current: 当前页码。
        :param size: 每页数量。
        :param sort_type: 排序类型。
        :return: 总数、当前页图片列表和可复用的评论数映射。
        """
        picture_ids = list(await qp.order_by("-id").values_list("id", flat=True))
        if not picture_ids:
            return 0, [], {}
        picture_comment_count_map = None
        if sort_type == "comment":
            picture_comment_count_map = await self.comment_dao.get_comment_count_map(
                picture_ids, ObjectTypeEnum.PICTURE
            )
            sorted_picture_ids = sorted(
                picture_ids,
                key=lambda picture_id: (picture_comment_count_map.get(picture_id, 0), picture_id),
                reverse=True,
            )
        else:
            picture_like_counts = await asyncio.gather(
                *[self.redis_util.Picture.get_like_count(picture_id) for picture_id in picture_ids]
            )
            picture_like_count_map = dict(zip(picture_ids, picture_like_counts))
            sorted_picture_ids = sorted(
                picture_ids,
                key=lambda picture_id: (picture_like_count_map.get(picture_id, 0), picture_id),
                reverse=True,
            )
        current = current if current > 0 else 1
        size = size if size > 0 else 10
        page_picture_ids = sorted_picture_ids[(current - 1) * size : current * size]
        if not page_picture_ids:
            return len(picture_ids), [], picture_comment_count_map
        picture_map = {picture.id: picture for picture in await Picture.filter(id__in=page_picture_ids).all()}
        return (
            len(picture_ids),
            [picture_map[picture_id] for picture_id in page_picture_ids if picture_id in picture_map],
            picture_comment_count_map,
        )

    async def _build_picture_records(
        self, pictures: list[Picture], user_id: int | None, picture_comment_count_map: dict[int, int] | None = None
    ) -> list[PictureDTO]:
        """
        组装图片 DTO 的用户、点赞数、评论数和登录用户点赞状态。

        :param pictures: 图片模型列表。
        :param user_id: 当前登录用户 ID。
        :param picture_comment_count_map: 可复用的图片评论数量映射。
        :return: 图片 DTO 列表。
        """
        records = PictureDTO.bulk_model_validate(pictures)
        if picture_comment_count_map is None:
            picture_comment_count_map = await self.comment_dao.get_comment_count_map(
                [picture.id for picture in records], ObjectTypeEnum.PICTURE
            )
        for picture in records:
            picture.user = await manager.get_user_info(picture.user_id, UserBaseInfoDTO)
            picture.like_count = await self.redis_util.Picture.get_like_count(picture.id)
            picture.comment_count = picture_comment_count_map.get(picture.id, 0)
            picture.has_like = await self.redis_util.Picture.has_like(user_id, picture.id)
        return records

    async def add_picture(self, picture_add_vo: PictureAddVO):
        """
        添加图片
        :param picture_add_vo:
        :return:
        """
        is_exists = await PictureAlbum.filter(id=picture_add_vo.album_id, status=CheckStatusEnum.PASS).exists()
        if not is_exists:
            raise MyException(ErrorCode.PICTURE_ALBUM_NOT_EXIST)
        user_id = ContextVars.token_user_id.get()
        picture = Picture(**picture_add_vo.model_dump(exclude_none=True))
        picture.user_id = user_id
        picture.status = CheckStatusEnum.PASS  # 目前默认无需审核
        if not picture.thumb_url:
            picture.thumb_url = picture.url
        await picture.save()

    async def update_picture(self, picture_update_vo: PictureUpdateVO):
        """
        更新图片信息
        :param picture_update_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        if picture_update_vo.album_id:
            is_exists = await PictureAlbum.filter(
                id=picture_update_vo.album_id, user_id=user_id, status=CheckStatusEnum.PASS
            ).exists()
            if not is_exists:
                raise MyException(ErrorCode.PICTURE_ALBUM_NOT_EXIST)
        if picture_update_vo.url and not (
            picture_update_vo.width or picture_update_vo.height or picture_update_vo.size
        ):
            raise MyException(ErrorCode.PARAM_ERROR)
        picture = await Picture.filter(
            ~Q(status=CheckStatusEnum.REJECT), id=picture_update_vo.id, user_id=user_id
        ).first()
        if not picture:
            raise MyException(ErrorCode.PICTURE_NOT_EXIST)
        update_dict = picture_update_vo.model_dump(exclude_none=True, exclude={"id"})
        if "url" in update_dict and not update_dict.get("thumb_url"):
            update_dict["thumb_url"] = update_dict["url"]
        await picture.update_from_dict(update_dict)
        await picture.save(update_fields=update_dict.keys())

    async def delete_picture(self, batch_vo: BatchVO):
        """
        删除图片
        :param batch_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        q = Picture.filter(~Q(status=CheckStatusEnum.CHECKING), id__in=batch_vo.ids, user_id=user_id)
        pictures = await q.all()
        urls = []
        picture_ids = []
        for picture in pictures:
            urls.append(picture.url)
            urls.append(picture.thumb_url)
            picture_ids.append(picture.id)
        async with in_transaction():
            # 删除图片和评论
            await self.source_service.change_source_status(urls, user_id)
            await q.delete()
            await self.comment_dao.clear_comment(picture_ids, obj_type=ObjectTypeEnum.PICTURE)
