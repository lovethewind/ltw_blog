from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.core.sqlalchemy.base_model import BaseModel
from apps.base.enum.common import CheckStatusEnum
from apps.base.enum.picture import AlbumTypeEnum


class Picture(BaseModel):
    """
    图片模型。
    """

    __tablename__ = "t_picture"
    __table_args__ = {"comment": "图片表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    album_id: Mapped[int] = mapped_column(BigInteger, comment="图册id")
    description: Mapped[str] = mapped_column(String(200), default="", comment="说明")
    url: Mapped[str] = mapped_column(String(512), comment="图片地址")
    thumb_url: Mapped[str] = mapped_column(String(512), default="", comment="图片缩略图")
    size: Mapped[int] = mapped_column(Integer, default=0, comment="图片大小")
    width: Mapped[int] = mapped_column(Integer, default=0, comment="图片宽度")
    height: Mapped[int] = mapped_column(Integer, default=0, comment="图片高度")
    like_count: Mapped[int] = mapped_column(BigInteger, default=0, comment="点赞量")
    comment_count: Mapped[int] = mapped_column(BigInteger, default=0, comment="评论量")
    status: Mapped[int] = mapped_column(
        Integer, default=CheckStatusEnum.PASS.value, comment="审核状态: 1: 已通过 2:审核中 3:拒绝"
    )


class PictureAlbum(BaseModel):
    """
    图册模型。
    """

    __tablename__ = "t_picture_album"
    __table_args__ = {"comment": "图册表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    name: Mapped[str] = mapped_column(String(20), comment="图册名")
    description: Mapped[str] = mapped_column(String(200), default="", comment="图册描述")
    cover: Mapped[str] = mapped_column(String(512), comment="图册封面")
    status: Mapped[int] = mapped_column(
        Integer, default=CheckStatusEnum.PASS.value, comment="审核状态: 1: 已通过 2:审核中 3:拒绝"
    )
    album_type: Mapped[int] = mapped_column(Integer, default=AlbumTypeEnum.PRIVATE.value, comment="类型 1公开 2私密")
