from tortoise import fields

from apps.base.enum.common import CheckStatusEnum
from apps.base.enum.picture import AlbumTypeEnum
from apps.base.models.base import BaseModel


class Picture(BaseModel):
    user_id = fields.BigIntField(description="用户id")
    album_id = fields.BigIntField(description="图册id")
    description = fields.CharField(max_length=200, default='', description="说明")
    url = fields.CharField(max_length=512, description="图片地址")
    size = fields.IntField(default=0, description="图片大小")
    width = fields.IntField(default=0, description="图片宽度")
    height = fields.IntField(default=0, description="图片高度")
    status = fields.IntEnumField(CheckStatusEnum, defalut=CheckStatusEnum.PASS,
                                 description="审核状态: 1: 已通过 2:审核中 3:拒绝")

    class Meta:
        table = "t_picture"
        table_description = "图片表"


class PictureAlbum(BaseModel):
    user_id = fields.BigIntField(description="用户id")
    name = fields.CharField(max_length=20, description="图册名")
    description = fields.CharField(max_length=200, default='', description="图册描述")
    cover = fields.CharField(max_length=512, description="图册封面")
    status = fields.IntEnumField(CheckStatusEnum, defalut=CheckStatusEnum.PASS,
                                 description="审核状态: 1: 已通过 2:审核中 3:拒绝")
    album_type = fields.IntEnumField(AlbumTypeEnum, defalut=AlbumTypeEnum.PRIVATE, description="类型 1公开 2私密")

    class Meta:
        table = "t_picture_album"
        table_description = "图册表"
