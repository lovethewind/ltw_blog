# @Time    : 2024/9/3 14:05
# @Author  : frank
# @File    : picture_service.py
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from apps.base.core.depend_inject import Component, Autowired
from apps.base.enum.action import ObjectTypeEnum
from apps.base.enum.common import CheckStatusEnum
from apps.base.enum.error_code import ErrorCode
from apps.base.enum.picture import AlbumTypeEnum
from apps.base.exception.my_exception import MyException
from apps.base.models.picture import PictureAlbum, Picture
from apps.base.utils.page_util import Pagination
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
from apps.web.vo.picture_vo import PictureQueryVO, PictureAddVO, PictureAlbumAddVO, PictureAlbumUpdateVO, \
    PictureUpdateVO


@Component()
class PictureService:
    user_dao: UserDao = Autowired()
    comment_dao: CommentDao = Autowired()
    picture_util: PictureUtil = Autowired()
    redis_util: RedisUtil = Autowired()
    source_service: SourceService = Autowired()

    async def list_album(self, current: int, size: int, is_user=False):
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
        page = await Pagination[PictureAlbumDTO](current, size, q).execute()
        return page

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
        picture_album = await PictureAlbum.filter(~Q(status=CheckStatusEnum.REJECT), id=picture_album_update_vo.id,
                                                  user_id=user_id).first()
        if not picture_album:
            raise MyException(ErrorCode.PICTURE_ALBUM_NOT_EXIST)
        if picture_album.album_type == AlbumTypeEnum.PUBLIC and picture_album_update_vo.album_type == AlbumTypeEnum.PRIVATE:
            # 无法公开转私密
            raise MyException(ErrorCode.PICTURE_ALBUM_IS_PUBLIC)
        await self.source_service.check_and_update_source_status(picture_album.cover, picture_album_update_vo.cover,
                                                                 user_id)
        update_dict = picture_album_update_vo.model_dump(exclude_none=True)
        await picture_album.update_from_dict(update_dict)
        await picture_album.save(update_fields=update_dict.keys())

    async def delete_album(self, album_id: int):
        """
        删除图库分类
        :param album_id:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        album = await PictureAlbum.filter(~Q(status=CheckStatusEnum.REJECT),
                                          album_type=AlbumTypeEnum.PRIVATE,
                                          id=album_id, user_id=user_id).first()
        if not album:
            raise MyException(ErrorCode.PICTURE_ALBUM_NOT_EXIST)
        q = Picture.filter(album_id=album_id)
        pictures = await q.all()
        urls = []
        picture_ids = []
        for picture in pictures:
            urls.append(picture.url)
            picture_ids.append(picture.id)
        async with in_transaction():
            # 删除图库下的图片和评论
            await album.delete()
            await self.source_service.change_source_status(urls, user_id)
            await self.comment_dao.clear_comment(picture_ids, obj_type=ObjectTypeEnum.PICTURE)
            await q.delete()

    async def list_picture(self, current: int, size: int, picture_query_vo: PictureQueryVO, is_user=False):
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
        page = await Pagination[PictureDTO](current, size, qp).execute()
        for picture in page.records:
            picture.user = await manager.get_user_info(picture.user_id, UserBaseInfoDTO)
            picture.like_count = await self.redis_util.Picture.get_like_count(picture.id)
            picture.has_like = await self.redis_util.Picture.has_like(user_id, picture.id)
        return page

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
        await picture.save()

    async def update_picture(self, picture_update_vo: PictureUpdateVO):
        """
        更新图片信息
        :param picture_update_vo:
        :return: 
        """
        user_id = ContextVars.token_user_id.get()
        if picture_update_vo.album_id:
            is_exists = await PictureAlbum.filter(id=picture_update_vo.album_id, user_id=user_id,
                                                  status=CheckStatusEnum.PASS).exists()
            if not is_exists:
                raise MyException(ErrorCode.PICTURE_ALBUM_NOT_EXIST)
        if picture_update_vo.url and not (picture_update_vo.width or
                                          picture_update_vo.height or
                                          picture_update_vo.size):
            raise MyException(ErrorCode.PARAM_ERROR)
        picture = await Picture.filter(~Q(status=CheckStatusEnum.REJECT), id=picture_update_vo.id,
                                       user_id=user_id).first()
        if not picture:
            raise MyException(ErrorCode.PICTURE_NOT_EXIST)
        update_dict = picture_update_vo.model_dump(exclude_none=True)
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
            picture_ids.append(picture.id)
        async with in_transaction():
            # 删除图片和评论
            await self.source_service.change_source_status(urls, user_id)
            await q.delete()
            await self.comment_dao.clear_comment(picture_ids, obj_type=ObjectTypeEnum.PICTURE)
