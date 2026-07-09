import asyncio
from datetime import datetime

from sqlalchemy import ColumnElement, case, func, select

from apps.base.core.depend_inject import Autowired, Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.article import ArticleStatusEnum
from apps.base.enum.error_code import ErrorCode
from apps.base.enum.user import UserSettingsEnum
from apps.base.exception.my_exception import MyException
from apps.base.models.article import Article
from apps.base.utils.picture_util import PictureUtil
from apps.base.utils.redis_util import RedisUtil
from apps.web.core.context_vars import ContextVars
from apps.web.core.es.constant.es_constant import ESConstant
from apps.web.core.es.utils.es_util import ESUtil
from apps.web.dao.article_dao import ArticleDao
from apps.web.dao.user_dao import UserDao
from apps.web.dto.article_dto import ArticleBaseInfoDTO, ArticleDTO, ArticleListDTO
from apps.web.dto.user_dto import UserBaseInfoDTO, UserSimpleInfoDTO
from apps.web.service.source_service import SourceService
from apps.web.utils.ws_util import manager
from apps.web.vo.article_vo import ArticleAddViewCountVO, ArticleQueryVO, ArticleUpdateVO, ArticleVO, OrderTypeEnum
from apps.web.vo.batch_vo import BatchVO


@Component()
class ArticleService:
    source_service: SourceService = Autowired()
    redis_util: RedisUtil = Autowired()
    picture_util: PictureUtil = Autowired()
    es_util: ESUtil = Autowired()
    user_dao: UserDao = Autowired()
    article_dao: ArticleDao = Autowired()

    async def list_articles(self, current: int, size: int, article_query_vo: ArticleQueryVO) -> dict:
        """
        分页及查询获取文章列表
        :param current:
        :param size:
        :param article_query_vo:
        :return:
        """
        login_user_id = ContextVars.token_user_id.get()
        filters: list[ColumnElement] = [Article.is_deleted.is_(False)]
        if article_query_vo.keyword:
            filters.append(Article.title.icontains(article_query_vo.keyword))
        if article_query_vo.category_id:
            filters.append(Article.category_id == article_query_vo.category_id)
        if article_query_vo.is_original is not None:
            filters.append(Article.is_original == article_query_vo.is_original)
        if article_query_vo.tag_id:
            filters.append(Article.tag_list.contains([article_query_vo.tag_id]))
        if article_query_vo.user_id:
            filters.append(Article.user_id == article_query_vo.user_id)
            if article_query_vo.user_id != login_user_id:  # 非本人查询，只返回已发布的文章
                # 检查对方是否允许查看
                if not article_query_vo.user_id:
                    return {"total": 0, "records": []}
                user_setting_value = await self.user_dao.get_user_setting_value(
                    article_query_vo.user_id, UserSettingsEnum.ALLOW_VIEW_MY_ARTICLE
                )
                user_setting_value = bool(user_setting_value)
                if not user_setting_value:
                    return {"total": 0, "records": []}
                filters.append(Article.status == ArticleStatusEnum.PUBLISHED)
            elif article_query_vo.status:
                filters.append(Article.status == article_query_vo.status)
        else:
            filters.append(Article.status == ArticleStatusEnum.PUBLISHED)
        if article_query_vo.date_from and article_query_vo.date_to:
            filters.append(Article.create_time.between(article_query_vo.date_from, article_query_vo.date_to))
        offset, limit = db.page(current, size)
        total_stmt = select(func.count()).select_from(Article).where(*filters)
        stmt = select(Article).where(*filters)
        match article_query_vo.order_type:
            case OrderTypeEnum.BY_VIEW_COUNT:
                # 按热度排序
                total, article_ids = await asyncio.gather(
                    db.scalar(total_stmt),
                    self.redis_util.Article.get_published_article(current, size),
                )
                if not article_ids:
                    return {"total": total, "records": []}
                ordering = case({article_id: index for index, article_id in enumerate(article_ids)}, value=Article.id)
                stmt = stmt.where(Article.id.in_(article_ids)).order_by(ordering)
                records = await self.article_dao.get_article_detail_by_ids(articles=await db.model_all(stmt))
                return {"total": total, "records": records}
            case OrderTypeEnum.BY_CREATE_TIME_ASC:
                stmt = stmt.order_by(Article.id.asc())
            case _:
                stmt = stmt.order_by(Article.id.desc())
        total, articles = await asyncio.gather(
            db.scalar(total_stmt),
            db.model_all(stmt.offset(offset).limit(limit)),
        )
        records = await self.article_dao.get_article_detail_by_ids(articles=articles)
        return {"total": total, "records": records}

    async def add(self, article_vo: ArticleVO) -> int:
        """
        添加文章

        :param article_vo: 文章新增参数。
        :return: 新增文章 ID。
        """
        user_id = ContextVars.token_user_id.get()
        article = Article(**article_vo.model_dump())
        article.user_id = user_id
        if not article.cover:
            article.cover, article.cover_thumb = await self.picture_util.get_random_img_url(with_thumb=True)
        if not article.cover_thumb:
            article.cover_thumb = article.cover
        async with db.atomic() as session:
            session.add(article)
            await session.flush()
            await self._update_article_to_es(article)
        return article.id

    async def detail(self, article_id: int) -> ArticleDTO:
        """
        获取文章详情

        :param article_id: 文章 ID。
        :return: 文章详情 DTO。
        """
        article = await db.model_first(select(Article).where(Article.id == article_id))
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        # 获取前一篇和后一篇文章
        last_article, nex_article, newest_articles = await asyncio.gather(
            db.model_first(
                select(Article).where(Article.id < article_id, Article.status == ArticleStatusEnum.PUBLISHED)
            ),
            db.model_first(
                select(Article)
                .where(Article.id > article_id, Article.status == ArticleStatusEnum.PUBLISHED)
                .order_by(Article.id)
            ),
            db.model_all(
                select(Article).where(Article.id != article_id, Article.status == ArticleStatusEnum.PUBLISHED).limit(5)
            ),
        )
        # 获取推荐文章单独一个接口
        article_dto = ArticleDTO.model_validate(article, from_attributes=True)
        if last_article:
            article_dto.last_article = ArticleBaseInfoDTO.model_validate(last_article, from_attributes=True)
        if nex_article:
            article_dto.next_article = ArticleBaseInfoDTO.model_validate(nex_article, from_attributes=True)
        article_dto.newest_article_list = ArticleBaseInfoDTO.bulk_model_validate(newest_articles)
        article_dto.view_count, article_dto.like_count, article_dto.collect_count, article_dto.comment_count = (
            await asyncio.gather(
                self.redis_util.Article.get_article_view_count(article_id),
                self.redis_util.Article.get_article_like_count(article_id),
                self.redis_util.Article.get_article_collect_count(article_id),
                self.redis_util.Article.get_article_comment_count(article_id),
            )
        )
        article_dto.user = await manager.get_user_info(article.user_id, UserBaseInfoDTO)
        return article_dto

    async def add_view_count(self, article_add_view_count_vo: ArticleAddViewCountVO) -> None:
        """
        增加文章访问量

        :param article_add_view_count_vo: 文章访问量新增参数。
        :return: None。
        """
        await self.redis_util.Article.incr_article_view_count(article_add_view_count_vo.article_id)

    async def edit_find(self, article_id: int) -> ArticleDTO:
        """
        编辑文章时获取文章信息

        :param article_id: 文章 ID。
        :return: 文章详情 DTO。
        """
        user_id = ContextVars.token_user_id.get()
        article = await db.model_first(
            select(Article).where(Article.id == article_id, Article.user_id == user_id, Article.is_deleted.is_(False))
        )
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        ret = ArticleDTO.model_validate(article, from_attributes=True)
        return ret

    async def update(self, article_update_vo: ArticleUpdateVO) -> None:
        """
        更新文章

        :param article_update_vo: 文章更新参数。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        article = await db.model_first(
            select(Article).where(Article.id == article_update_vo.id, Article.user_id == user_id)
        )
        if not article:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        if article.status == ArticleStatusEnum.CHECKING:
            raise MyException(ErrorCode.PARAM_ERROR)
        # 删除旧资源
        old_cover_urls = {article.cover, article.cover_thumb}
        new_cover_urls = set()
        if article_update_vo.cover is not None:
            new_cover_urls.add(article_update_vo.cover)
        else:
            new_cover_urls.add(article.cover)
        if article_update_vo.cover_thumb is not None:
            new_cover_urls.add(article_update_vo.cover_thumb)
        else:
            new_cover_urls.add(article.cover_thumb)
        await self.source_service.check_and_update_source_status(old_cover_urls, new_cover_urls, user_id)
        # 删除旧附件
        old_attach_urls = {item.get("url") for item in article.attach_list}
        new_attach_urls = set()
        if article_update_vo.attach_list is not None:
            new_attach_urls = {item.get("url") for item in article_update_vo.attach_list}
        await self.source_service.check_and_update_source_status(old_attach_urls, new_attach_urls, user_id)
        article.edit_time = datetime.now()
        update_dict = article_update_vo.model_dump(exclude_none=True, exclude={"id"})
        if "cover" in update_dict and not update_dict.get("cover_thumb"):
            update_dict["cover_thumb"] = update_dict["cover"]
        for key, value in update_dict.items():
            setattr(article, key, value)
        async with db.atomic() as session:
            session.add(article)
            await session.flush()
            await self._update_article_to_es(article)

    async def article_count_info(self, article_query_vo: ArticleQueryVO) -> dict[int, int]:
        """
        获取文章数量信息

        :param article_query_vo: 文章查询参数。
        :return: 状态到数量的映射。
        """
        user_id = ContextVars.token_user_id.get()
        filters = [Article.user_id == user_id, Article.is_deleted.is_(False)]
        if article_query_vo.is_original is not None:
            filters.append(Article.is_original == article_query_vo.is_original)
        if article_query_vo.keyword:
            filters.append(Article.title.icontains(article_query_vo.keyword))
        if article_query_vo.date_from and article_query_vo.date_to:
            filters.append(Article.create_time.between(article_query_vo.date_from, article_query_vo.date_to))
        count_info_list = await db.all(
            select(Article.status, func.count(Article.id).label("article_count"))
            .where(*filters)
            .group_by(Article.status)
        )
        count_info_dict = {item.status: item.article_count for item in count_info_list}
        ret = {
            key.value: count_info_dict.get(key.value, 0) for key in ArticleStatusEnum.__dict__["_member_map_"].values()
        }
        return ret

    async def remove_to_recycle(self, batch_vo: BatchVO) -> None:
        """
        移动文章至回收站

        :param batch_vo: 批量文章 ID。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        article = await db.model_first(
            select(Article).where(
                Article.id.in_(batch_vo.ids), Article.user_id == user_id, Article.is_deleted.is_(False)
            )
        )
        if not article:
            return
        article.status = ArticleStatusEnum.DELETED
        async with db.atomic() as session:
            session.add(article)
            await session.flush()
            await self._update_article_to_es(article)

    async def remove_from_recycle(self, batch_vo: BatchVO) -> None:
        """
        删除回收站的文章

        :param batch_vo: 批量文章 ID。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        article = await db.model_first(
            select(Article).where(
                Article.id.in_(batch_vo.ids), Article.user_id == user_id, Article.status == ArticleStatusEnum.DELETED
            )
        )
        if not article:
            return
        article.is_deleted = True
        async with db.atomic() as session:
            session.add(article)
            await session.flush()
            await self._update_article_to_es(article)

    async def move_to_draft(self, batch_vo: BatchVO) -> None:
        """
        将回收站的文章恢复至草稿箱

        :param batch_vo: 批量文章 ID。
        :return: None。
        """
        user_id = ContextVars.token_user_id.get()
        article = await db.model_first(
            select(Article).where(
                Article.id.in_(batch_vo.ids),
                Article.user_id == user_id,
                Article.status == ArticleStatusEnum.DELETED,
                Article.is_deleted.is_(False),
            )
        )
        if not article:
            return
        article.status = ArticleStatusEnum.DRAFT
        async with db.atomic() as session:
            session.add(article)
            await session.flush()
            await self._update_article_to_es(article)

    async def _update_article_to_es(self, article: Article) -> None:
        """
        同步文章到 ES。

        :param article: 文章模型。
        :return: None。
        """
        item = ArticleListDTO.model_validate(article, from_attributes=True)
        item.user = await manager.get_user_info(article.user_id, UserSimpleInfoDTO)
        await self.es_util.client.index(index=ESConstant.ARTICLE_INDEX, id=article.id, document=item.model_dump())
