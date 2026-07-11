from typing import Any, TypeVar

from sqlalchemy import Select, delete, func, or_, select, update

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.base_model import BaseModel
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.article import Article
from apps.base.models.category import Category, Tag
from apps.base.models.comment import Comment
from apps.base.models.config import Config
from apps.base.models.link import Link
from apps.base.models.message import Message
from apps.base.models.picture import Picture, PictureAlbum
from apps.base.models.user import User
from apps.base.models.website import Website, WebsiteCategory

T = TypeVar("T", bound=BaseModel)


async def _paginate(stmt: Select[tuple[T]], current: int, size: int, *order_by: Any) -> tuple[list[T], int]:
    """
    执行后台列表分页查询。

    :param stmt: 查询语句。
    :param current: 当前页码。
    :param size: 每页条数。
    :param order_by: 排序字段。
    :return: 数据列表和总数。
    """
    offset, limit = db.page(current, size)
    total = await db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    records = await db.model_all(stmt.order_by(*order_by).offset(offset).limit(limit))
    return list(records), int(total or 0)


async def _create(model: type[T], data: dict[str, Any]) -> T:
    """
    创建后台管理模型。

    :param model: 模型类。
    :param data: 创建数据。
    :return: 创建后的模型对象。
    """
    item = model(**data)
    async with db.atomic() as session:
        session.add(item)
        await session.flush()
        await session.refresh(item)
    return item


async def _update(item: T, data: dict[str, Any]) -> T:
    """
    更新后台管理模型。

    :param item: 模型对象。
    :param data: 更新数据。
    :return: 更新后的模型对象。
    """
    if not data:
        return item
    for key, value in data.items():
        setattr(item, key, value)
    await db.execute(update(type(item)).where(type(item).id == item.id).values(**data))
    return item


async def _delete(model: type[T], item_id: int) -> None:
    """
    根据主键删除后台管理模型。

    :param model: 模型类。
    :param item_id: 主键 ID。
    :return: None。
    """
    await db.execute(delete(model).where(model.id == item_id))


@Component()
class AdminContentDao:
    """
    后台内容管理数据访问对象。
    """

    async def list_articles(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        category_id: int | None = None,
        status: int | None = None,
        user_id: int | None = None,
        is_original: bool | None = None,
    ) -> tuple[list[Article], int]:
        """
        分页查询文章。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 标题关键词。
        :param category_id: 分类 ID。
        :param status: 文章状态。
        :param user_id: 用户 ID。
        :param is_original: 是否原创。
        :return: 文章列表和总数。
        """
        stmt = select(Article)
        if keyword:
            stmt = stmt.where(or_(Article.title.ilike(f"%{keyword}%"), Article.content.ilike(f"%{keyword}%")))
        if category_id:
            stmt = stmt.where(Article.category_id == category_id)
        if status is not None:
            stmt = stmt.where(Article.status == status)
        if user_id:
            stmt = stmt.where(Article.user_id == user_id)
        if is_original is not None:
            stmt = stmt.where(Article.is_original == is_original)
        return await _paginate(stmt, current, size, Article.id.desc())

    async def list_article_authors(self, user_ids: list[int]) -> dict[int, User]:
        """
        批量查询文章作者。

        :param user_ids: 用户 ID 列表。
        :return: 用户 ID 到用户对象的映射。
        """
        if not user_ids:
            return {}
        users = await db.model_all(select(User).where(User.id.in_(user_ids)))
        return {user.id: user for user in users}

    async def get_article_by_id(self, article_id: int) -> Article | None:
        """
        根据 ID 查询文章。

        :param article_id: 文章 ID。
        :return: 文章对象。
        """
        return await db.model_first(select(Article).where(Article.id == article_id))

    async def create_article(self, data: dict[str, Any]) -> Article:
        """
        创建文章。

        :param data: 文章数据。
        :return: 文章对象。
        """
        return await _create(Article, data)

    async def update_article(self, article: Article, data: dict[str, Any]) -> Article:
        """
        更新文章。

        :param article: 文章对象。
        :param data: 更新数据。
        :return: 文章对象。
        """
        return await _update(article, data)

    async def delete_article(self, article_id: int) -> None:
        """
        删除文章。

        :param article_id: 文章 ID。
        :return: None。
        """
        await _delete(Article, article_id)

    async def list_comments(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        obj_id: int | None = None,
        obj_type: int | None = None,
        status: int | None = None,
        user_id: int | None = None,
    ) -> tuple[list[Comment], int]:
        """
        分页查询评论。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 评论内容关键词。
        :param obj_id: 对象 ID。
        :param obj_type: 对象类型。
        :param status: 评论状态。
        :param user_id: 用户 ID。
        :return: 评论列表和总数。
        """
        stmt = select(Comment)
        if keyword:
            stmt = stmt.where(Comment.content.ilike(f"%{keyword}%"))
        if obj_id:
            stmt = stmt.where(Comment.obj_id == obj_id)
        if obj_type is not None:
            stmt = stmt.where(Comment.obj_type == obj_type)
        if status is not None:
            stmt = stmt.where(Comment.status == status)
        if user_id:
            stmt = stmt.where(Comment.user_id == user_id)
        return await _paginate(stmt, current, size, Comment.id.desc())

    async def get_comment_by_id(self, comment_id: int) -> Comment | None:
        """
        根据 ID 查询评论。

        :param comment_id: 评论 ID。
        :return: 评论对象。
        """
        return await db.model_first(select(Comment).where(Comment.id == comment_id))

    async def update_comment(self, comment: Comment, data: dict[str, Any]) -> Comment:
        """
        更新评论。

        :param comment: 评论对象。
        :param data: 更新数据。
        :return: 评论对象。
        """
        return await _update(comment, data)

    async def delete_comment(self, comment_id: int) -> None:
        """
        删除评论。

        :param comment_id: 评论 ID。
        :return: None。
        """
        await _delete(Comment, comment_id)

    async def list_messages(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        user_id: int | None = None,
        parent_id: int | None = None,
    ) -> tuple[list[Message], int]:
        """
        分页查询留言。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 留言内容、昵称或邮箱关键词。
        :param user_id: 用户 ID。
        :param parent_id: 父留言 ID。
        :return: 留言列表和总数。
        """
        stmt = select(Message)
        if keyword:
            stmt = stmt.where(
                or_(
                    Message.content.ilike(f"%{keyword}%"),
                    Message.nickname.ilike(f"%{keyword}%"),
                    Message.email.ilike(f"%{keyword}%"),
                )
            )
        if user_id:
            stmt = stmt.where(Message.user_id == user_id)
        if parent_id is not None:
            stmt = stmt.where(Message.parent_id == parent_id)
        return await _paginate(stmt, current, size, Message.id.desc())

    async def get_message_by_id(self, message_id: int) -> Message | None:
        """
        根据 ID 查询留言。

        :param message_id: 留言 ID。
        :return: 留言对象。
        """
        return await db.model_first(select(Message).where(Message.id == message_id))

    async def update_message(self, message: Message, data: dict[str, Any]) -> Message:
        """
        更新留言。

        :param message: 留言对象。
        :param data: 更新数据。
        :return: 留言对象。
        """
        return await _update(message, data)

    async def delete_message(self, message_id: int) -> None:
        """
        删除留言。

        :param message_id: 留言 ID。
        :return: None。
        """
        await _delete(Message, message_id)

    async def list_categories(self) -> list[Category]:
        """
        查询分类列表。

        :return: 分类列表。
        """
        return list(await db.model_all(select(Category).order_by(Category.index, Category.id.desc())))

    async def get_category_by_id(self, category_id: int) -> Category | None:
        """
        根据 ID 查询分类。

        :param category_id: 分类 ID。
        :return: 分类对象。
        """
        return await db.model_first(select(Category).where(Category.id == category_id))

    async def create_category(self, data: dict[str, Any]) -> Category:
        """
        创建分类。

        :param data: 分类数据。
        :return: 分类对象。
        """
        return await _create(Category, data)

    async def update_category(self, category: Category, data: dict[str, Any]) -> Category:
        """
        更新分类。

        :param category: 分类对象。
        :param data: 更新数据。
        :return: 分类对象。
        """
        return await _update(category, data)

    async def delete_category(self, category_id: int) -> None:
        """
        删除分类。

        :param category_id: 分类 ID。
        :return: None。
        """
        await _delete(Category, category_id)

    async def list_tags(self, active_only: bool = False) -> list[Tag]:
        """
        查询标签列表。

        :param active_only: 是否只查询启用标签。
        :return: 标签列表。
        """
        stmt = select(Tag)
        if active_only:
            stmt = stmt.where(Tag.is_active.is_(True))
        return list(await db.model_all(stmt.order_by(Tag.index, Tag.id.desc())))

    async def get_tag_by_id(self, tag_id: int) -> Tag | None:
        """
        根据 ID 查询标签。

        :param tag_id: 标签 ID。
        :return: 标签对象。
        """
        return await db.model_first(select(Tag).where(Tag.id == tag_id))

    async def create_tag(self, data: dict[str, Any]) -> Tag:
        """
        创建标签。

        :param data: 标签数据。
        :return: 标签对象。
        """
        return await _create(Tag, data)

    async def update_tag(self, tag: Tag, data: dict[str, Any]) -> Tag:
        """
        更新标签。

        :param tag: 标签对象。
        :param data: 更新数据。
        :return: 标签对象。
        """
        return await _update(tag, data)

    async def delete_tag(self, tag_id: int) -> None:
        """
        删除标签。

        :param tag_id: 标签 ID。
        :return: None。
        """
        await _delete(Tag, tag_id)

    async def has_tag_children(self, tag_id: int) -> bool:
        """
        判断标签是否存在子级。

        :param tag_id: 标签 ID。
        :return: 是否存在子级。
        """
        return bool(await db.scalar(select(func.count(Tag.id)).where(Tag.parent_id == tag_id)))

    async def list_picture_albums(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        status: int | None = None,
        album_type: int | None = None,
        user_id: int | None = None,
    ) -> tuple[list[PictureAlbum], int]:
        """
        分页查询图册。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 图册关键词。
        :param status: 审核状态。
        :param album_type: 图册类型。
        :param user_id: 用户 ID。
        :return: 图册列表和总数。
        """
        stmt = select(PictureAlbum)
        if keyword:
            stmt = stmt.where(
                or_(PictureAlbum.name.ilike(f"%{keyword}%"), PictureAlbum.description.ilike(f"%{keyword}%"))
            )
        if status is not None:
            stmt = stmt.where(PictureAlbum.status == status)
        if album_type is not None:
            stmt = stmt.where(PictureAlbum.album_type == album_type)
        if user_id:
            stmt = stmt.where(PictureAlbum.user_id == user_id)
        return await _paginate(stmt, current, size, PictureAlbum.id.desc())

    async def get_picture_album_by_id(self, album_id: int) -> PictureAlbum | None:
        """
        根据 ID 查询图册。

        :param album_id: 图册 ID。
        :return: 图册对象。
        """
        return await db.model_first(select(PictureAlbum).where(PictureAlbum.id == album_id))

    async def create_picture_album(self, data: dict[str, Any]) -> PictureAlbum:
        """
        创建图册。

        :param data: 图册数据。
        :return: 图册对象。
        """
        return await _create(PictureAlbum, data)

    async def update_picture_album(self, album: PictureAlbum, data: dict[str, Any]) -> PictureAlbum:
        """
        更新图册。

        :param album: 图册对象。
        :param data: 更新数据。
        :return: 图册对象。
        """
        return await _update(album, data)

    async def delete_picture_album(self, album_id: int) -> None:
        """
        删除图册。

        :param album_id: 图册 ID。
        :return: None。
        """
        await _delete(PictureAlbum, album_id)

    async def list_pictures(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        album_id: int | None = None,
        status: int | None = None,
        user_id: int | None = None,
    ) -> tuple[list[Picture], int]:
        """
        分页查询图片。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 图片说明关键词。
        :param album_id: 图册 ID。
        :param status: 审核状态。
        :param user_id: 用户 ID。
        :return: 图片列表和总数。
        """
        stmt = select(Picture)
        if keyword:
            stmt = stmt.where(Picture.description.ilike(f"%{keyword}%"))
        if album_id:
            stmt = stmt.where(Picture.album_id == album_id)
        if status is not None:
            stmt = stmt.where(Picture.status == status)
        if user_id:
            stmt = stmt.where(Picture.user_id == user_id)
        return await _paginate(stmt, current, size, Picture.id.desc())

    async def get_picture_by_id(self, picture_id: int) -> Picture | None:
        """
        根据 ID 查询图片。

        :param picture_id: 图片 ID。
        :return: 图片对象。
        """
        return await db.model_first(select(Picture).where(Picture.id == picture_id))

    async def create_picture(self, data: dict[str, Any]) -> Picture:
        """
        创建图片。

        :param data: 图片数据。
        :return: 图片对象。
        """
        return await _create(Picture, data)

    async def update_picture(self, picture: Picture, data: dict[str, Any]) -> Picture:
        """
        更新图片。

        :param picture: 图片对象。
        :param data: 更新数据。
        :return: 图片对象。
        """
        return await _update(picture, data)

    async def delete_picture(self, picture_id: int) -> None:
        """
        删除图片。

        :param picture_id: 图片 ID。
        :return: None。
        """
        await _delete(Picture, picture_id)

    async def list_links(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        status: int | None = None,
    ) -> tuple[list[Link], int]:
        """
        分页查询友链。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 友链关键词。
        :param status: 审核状态。
        :return: 友链列表和总数。
        """
        stmt = select(Link)
        if keyword:
            stmt = stmt.where(
                or_(Link.name.ilike(f"%{keyword}%"), Link.url.ilike(f"%{keyword}%"), Link.email.ilike(f"%{keyword}%"))
            )
        if status is not None:
            stmt = stmt.where(Link.status == status)
        return await _paginate(stmt, current, size, Link.index, Link.id.desc())

    async def get_link_by_id(self, link_id: int) -> Link | None:
        """
        根据 ID 查询友链。

        :param link_id: 友链 ID。
        :return: 友链对象。
        """
        return await db.model_first(select(Link).where(Link.id == link_id))

    async def create_link(self, data: dict[str, Any]) -> Link:
        """
        创建友链。

        :param data: 友链数据。
        :return: 友链对象。
        """
        return await _create(Link, data)

    async def update_link(self, link: Link, data: dict[str, Any]) -> Link:
        """
        更新友链。

        :param link: 友链对象。
        :param data: 更新数据。
        :return: 友链对象。
        """
        return await _update(link, data)

    async def delete_link(self, link_id: int) -> None:
        """
        删除友链。

        :param link_id: 友链 ID。
        :return: None。
        """
        await _delete(Link, link_id)

    async def list_website_categories(self) -> list[WebsiteCategory]:
        """
        查询网站导航分类列表。

        :return: 网站导航分类列表。
        """
        return list(
            await db.model_all(select(WebsiteCategory).order_by(WebsiteCategory.index, WebsiteCategory.id.desc()))
        )

    async def get_website_category_by_id(self, category_id: int) -> WebsiteCategory | None:
        """
        根据 ID 查询网站导航分类。

        :param category_id: 网站导航分类 ID。
        :return: 网站导航分类对象。
        """
        return await db.model_first(select(WebsiteCategory).where(WebsiteCategory.id == category_id))

    async def create_website_category(self, data: dict[str, Any]) -> WebsiteCategory:
        """
        创建网站导航分类。

        :param data: 网站导航分类数据。
        :return: 网站导航分类对象。
        """
        return await _create(WebsiteCategory, data)

    async def update_website_category(self, category: WebsiteCategory, data: dict[str, Any]) -> WebsiteCategory:
        """
        更新网站导航分类。

        :param category: 网站导航分类对象。
        :param data: 更新数据。
        :return: 网站导航分类对象。
        """
        return await _update(category, data)

    async def delete_website_category(self, category_id: int) -> None:
        """
        删除网站导航分类。

        :param category_id: 网站导航分类 ID。
        :return: None。
        """
        await _delete(WebsiteCategory, category_id)

    async def list_websites(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        category_id: int | None = None,
        status: int | None = None,
        user_id: int | None = None,
    ) -> tuple[list[Website], int]:
        """
        分页查询网站导航。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 网站关键词。
        :param category_id: 分类 ID。
        :param status: 审核状态。
        :param user_id: 用户 ID。
        :return: 网站导航列表和总数。
        """
        stmt = select(Website)
        if keyword:
            stmt = stmt.where(
                or_(
                    Website.name.ilike(f"%{keyword}%"),
                    Website.url.ilike(f"%{keyword}%"),
                    Website.introduce.ilike(f"%{keyword}%"),
                )
            )
        if category_id:
            stmt = stmt.where(Website.category_id == category_id)
        if status is not None:
            stmt = stmt.where(Website.status == status)
        if user_id:
            stmt = stmt.where(Website.user_id == user_id)
        return await _paginate(stmt, current, size, Website.index, Website.id.desc())

    async def get_website_by_id(self, website_id: int) -> Website | None:
        """
        根据 ID 查询网站导航。

        :param website_id: 网站导航 ID。
        :return: 网站导航对象。
        """
        return await db.model_first(select(Website).where(Website.id == website_id))

    async def create_website(self, data: dict[str, Any]) -> Website:
        """
        创建网站导航。

        :param data: 网站导航数据。
        :return: 网站导航对象。
        """
        return await _create(Website, data)

    async def update_website(self, website: Website, data: dict[str, Any]) -> Website:
        """
        更新网站导航。

        :param website: 网站导航对象。
        :param data: 更新数据。
        :return: 网站导航对象。
        """
        return await _update(website, data)

    async def delete_website(self, website_id: int) -> None:
        """
        删除网站导航。

        :param website_id: 网站导航 ID。
        :return: None。
        """
        await _delete(Website, website_id)

    async def list_configs(
        self,
        current: int,
        size: int,
        keyword: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Config], int]:
        """
        分页查询配置。

        :param current: 当前页码。
        :param size: 每页条数。
        :param keyword: 配置关键词。
        :param is_active: 是否启用。
        :return: 配置列表和总数。
        """
        stmt = select(Config)
        if keyword:
            stmt = stmt.where(or_(Config.name.ilike(f"%{keyword}%"), Config.description.ilike(f"%{keyword}%")))
        if is_active is not None:
            stmt = stmt.where(Config.is_active == is_active)
        return await _paginate(stmt, current, size, Config.id.desc())

    async def get_config_by_id(self, config_id: int) -> Config | None:
        """
        根据 ID 查询配置。

        :param config_id: 配置 ID。
        :return: 配置对象。
        """
        return await db.model_first(select(Config).where(Config.id == config_id))

    async def create_config(self, data: dict[str, Any]) -> Config:
        """
        创建配置。

        :param data: 配置数据。
        :return: 配置对象。
        """
        return await _create(Config, data)

    async def update_config(self, config: Config, data: dict[str, Any]) -> Config:
        """
        更新配置。

        :param config: 配置对象。
        :param data: 更新数据。
        :return: 配置对象。
        """
        return await _update(config, data)

    async def delete_config(self, config_id: int) -> None:
        """
        删除配置。

        :param config_id: 配置 ID。
        :return: None。
        """
        await _delete(Config, config_id)
