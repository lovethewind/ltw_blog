import asyncio
from datetime import datetime

from tortoise.expressions import Q
from tortoise.functions import Count
from tortoise.transactions import in_transaction

from apps.base.core.depend_inject import Component, Autowired
from apps.base.enum.article import ArticleStatusEnum
from apps.base.enum.error_code import ErrorCode
from apps.base.enum.user import UserSettingsEnum
from apps.base.exception.my_exception import MyException
from apps.base.models.article import Article
from apps.base.utils.page_util import PageResult, Pagination
from apps.base.utils.picture_util import PictureUtil
from apps.base.utils.redis_util import RedisUtil
from apps.web.core.context_vars import ContextVars
from apps.web.core.es.constant.es_constant import ESConstant
from apps.web.core.es.utils.es_util import ESUtil
from apps.web.dao.article_dao import ArticleDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.article_dto import ArticleDTO, ArticleBaseInfoDTO, ArticleListDTO
from apps.web.dto.user_dto import UserBaseInfoDTO, UserSimpleInfoDTO
from apps.web.service.source_service import SourceService
from apps.web.utils.ws_util import manager
from apps.web.vo.article_vo import ArticleQueryVO, OrderTypeEnum, ArticleVO, ArticleUpdateVO, ArticleAddViewCountVO
from apps.web.vo.batch_vo import BatchVO


@Component()
class ArticleService:
    source_service: SourceService = Autowired()
    redis_util: RedisUtil = Autowired()
    picture_util: PictureUtil = Autowired()
    es_util: ESUtil = Autowired()
    user_dao: UserDao = Autowired()
    article_dao: ArticleDao = Autowired()

    async def list_articles(self, current: int, size: int, article_query_vo: ArticleQueryVO):
        """
        分页及查询获取文章列表
        :param current:
        :param size:
        :param article_query_vo:
        :return:
        """
        login_user_id = ContextVars.token_user_id.get()
        q = Article.filter(is_deleted=False)
        if article_query_vo.keyword:
            q = q.filter(title__icontains=article_query_vo.keyword)
        if article_query_vo.category_id:
            q = q.filter(category_id=article_query_vo.category_id)
        if article_query_vo.is_original is not None:
            q = q.filter(is_original=article_query_vo.is_original)
        if article_query_vo.tag_id:
            q = q.filter(tag_list__contains=[article_query_vo.tag_id])
        if article_query_vo.user_id:
            q = q.filter(user_id=article_query_vo.user_id)
            if article_query_vo.user_id != login_user_id:  # 非本人查询，只返回已发布的文章
                # 检查对方是否允许查看
                user_setting_value = await self.user_dao.get_user_setting_value(article_query_vo.user_id,
                                                                                UserSettingsEnum.ALLOW_VIEW_MY_ARTICLE)
                if user_setting_value is False:
                    return PageResult[ArticleListDTO](current=current, size=size, total=0, records=[])
                q = q.filter(status=ArticleStatusEnum.PUBLISHED)
            elif article_query_vo.status:
                q = q.filter(status=article_query_vo.status)
        else:
            q = q.filter(status=ArticleStatusEnum.PUBLISHED)
        if article_query_vo.date_from and article_query_vo.date_to:
            q = q.filter(create_time__range=[article_query_vo.date_from, article_query_vo.date_to])
        q_count = q
        match article_query_vo.order_type:
            case OrderTypeEnum.BY_VIEW_COUNT:
                # 按热度排序
                article_ids = await self.redis_util.Article.get_published_article(current, size)
                q = q.filter(id__in=article_ids)
            case OrderTypeEnum.BY_CREATE_TIME_ASC:
                q = q.order_by("id")
            case _:
                q = q.offset((current - 1) * size).limit(size)
        page = await Pagination[ArticleListDTO](current, size, q, q_count=q_count).execute()
        page.records = await self.article_dao.get_article_detail_by_ids(articles=page.records)
        return page

    async def add(self, article_vo: ArticleVO):
        """
        添加文章
        :param article_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        article = Article(**article_vo.model_dump())
        article.user_id = user_id
        article.cover = await self.picture_util.get_random_img_url()
        async with in_transaction():
            await article.save()
            await self._update_article_to_es(article)
        return article.id

    async def detail(self, article_id: int):
        """
        获取文章详情
        :param article_id:
        :return:
        """
        article = await Article.filter(id=article_id).first()
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        # 获取前一篇和后一篇文章
        (
            last_article,
            nex_article,
            newest_articles
        ) = await asyncio.gather(
            Article.filter(id__lt=article_id, status=ArticleStatusEnum.PUBLISHED).first(),
            Article.filter(id__gt=article_id, status=ArticleStatusEnum.PUBLISHED).order_by("id").first(),
            Article.filter(~Q(id=article_id), status=ArticleStatusEnum.PUBLISHED).limit(5)
        )
        # 获取推荐文章单独一个接口
        article_dto = ArticleDTO.model_validate(article, from_attributes=True)
        article_dto.last_article = ArticleBaseInfoDTO.model_validate(last_article, from_attributes=True)
        article_dto.next_article = ArticleBaseInfoDTO.model_validate(nex_article, from_attributes=True)
        article_dto.newest_article_list = ArticleBaseInfoDTO.bulk_model_validate(newest_articles)
        (
            article_dto.view_count,
            article_dto.like_count,
            article_dto.collect_count,
            article_dto.comment_count
        ) = await asyncio.gather(
            self.redis_util.Article.get_article_view_count(article_id),
            self.redis_util.Article.get_article_like_count(article_id),
            self.redis_util.Article.get_article_collect_count(article_id),
            self.redis_util.Article.get_article_comment_count(article_id)
        )
        article_dto.user = await manager.get_user_info(article.user_id, UserBaseInfoDTO)
        return article_dto

    async def add_view_count(self, article_add_view_count_vo: ArticleAddViewCountVO):
        """
        增加文章访问量
        :param article_add_view_count_vo:
        :return:
        """
        await self.redis_util.Article.incr_article_view_count(article_add_view_count_vo.article_id)

    async def edit_find(self, article_id: int):
        """
        编辑文章时获取文章信息
        :param article_id:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        article = await Article.filter(id=article_id, user_id=user_id, is_deleted=False).first()
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        ret = ArticleDTO.model_validate(article, from_attributes=True)
        return ret

    async def update(self, article_update_vo: ArticleUpdateVO):
        """
        更新文章
        :param article_update_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        article = await Article.filter(id=article_update_vo.id, user_id=user_id).first()
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        if article.status == ArticleStatusEnum.CHECKING:
            raise MyException(ErrorCode.PARAM_ERROR)
        # 删除旧资源
        await self.source_service.check_and_update_source_status(article.cover, article_update_vo.cover, user_id)
        # 删除旧附件
        old_attach_urls = {item.get("url") for item in article.attach_list}
        new_attach_urls = set()
        if article_update_vo.attach_list is not None:
            new_attach_urls = {item.get("url") for item in article_update_vo.attach_list}
        await self.source_service.check_and_update_source_status(old_attach_urls, new_attach_urls, user_id)
        article.edit_time = datetime.now()
        update_dict = article_update_vo.model_dump(exclude_none=True)
        await article.update_from_dict(update_dict)
        async with in_transaction():
            await article.save(update_fields=update_dict.keys())
            await self._update_article_to_es(article)

    async def article_count_info(self, article_query_vo: ArticleQueryVO):
        """
        获取文章数量信息
        :param article_query_vo
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        q = Article.filter(user_id=user_id, is_deleted=False)
        if article_query_vo.is_original is not None:
            q = q.filter(is_original=article_query_vo.is_original)
        if article_query_vo.keyword:
            q = q.filter(title__icontains=article_query_vo.keyword)
        if article_query_vo.date_from and article_query_vo.date_to:
            q = q.filter(create_time__range=[article_query_vo.date_from, article_query_vo.date_to])
        count_info_list = await q.group_by("status").annotate(count=Count("id")).values("status", "count")
        count_info_dict = {item.get("status"): item.get("count") for item in count_info_list}
        ret = {key.value: count_info_dict.get(key.value, 0) for key in
               ArticleStatusEnum.__dict__["_member_map_"].values()}
        return ret

    async def remove_to_recycle(self, batch_vo: BatchVO):
        """
        移动文章至回收站
        :param batch_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        article = await Article.filter(id__in=batch_vo.ids, user_id=user_id, is_deleted=False).first()
        if not article:
            return
        article.status = ArticleStatusEnum.DELETED
        async with in_transaction():
            await article.save(update_fields=("status",))
            await self._update_article_to_es(article)

    async def remove_from_recycle(self, batch_vo: BatchVO):
        """
        删除回收站的文章
        :param batch_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        article = await Article.filter(id__in=batch_vo.ids, user_id=user_id, status=ArticleStatusEnum.DELETED).first()
        if not article:
            return
        article.is_deleted = True
        async with in_transaction():
            await article.save(update_fields=("is_deleted",))
            await self._update_article_to_es(article)

    async def move_to_draft(self, batch_vo: BatchVO):
        """
        将回收站的文章恢复至草稿箱
        :param batch_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        article = await Article.filter(id__in=batch_vo.ids, user_id=user_id, status=ArticleStatusEnum.DELETED,
                                       is_deleted=False).first()
        if not article:
            return
        article.status = ArticleStatusEnum.DRAFT
        async with in_transaction():
            await article.save(update_fields=("status",))
            await self._update_article_to_es(article)

    async def _update_article_to_es(self, article):
        item = ArticleListDTO.model_validate(article, from_attributes=True)
        item.user = await manager.get_user_info(article.user_id, UserSimpleInfoDTO)
        await self.es_util.client.index(index=ESConstant.ARTICLE_INDEX, id=article.id, document=item.model_dump())
