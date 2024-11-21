from tortoise import fields

from apps.base.enum.article import ArticleStatusEnum
from apps.base.models.base import BaseModel


class Article(BaseModel):
    user_id = fields.BigIntField(description="用户id")
    title = fields.CharField(max_length=100, description="标题")
    cover = fields.CharField(max_length=512, description="封面")
    category_id = fields.BigIntField(description="分类id")
    tag_list = fields.JSONField(default=[], description="标签id列表")
    attach_list = fields.JSONField(default=[], description="附件列表")
    content = fields.TextField(description="内容")
    is_markdown = fields.BooleanField(default=False, description="是否是markdown")
    is_original = fields.BooleanField(default=True, description="是否是原创")
    original_url = fields.CharField(max_length=512, description="原文链接")
    status = fields.IntEnumField(ArticleStatusEnum, default=ArticleStatusEnum.DRAFT,
                                 description="文章状态 1:草稿 2:已发布 3:待审核 4:回收站")
    is_deleted = fields.BooleanField(default=False, description="是否已删除(实现逻辑删除)")
    edit_time = fields.DatetimeField(null=True, description="最后编辑时间")

    class Meta:
        table = "t_article"
        table_description = "文章表"
