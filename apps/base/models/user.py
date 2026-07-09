from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.enum.user import GenderEnum
from apps.base.models.base import BaseModel


class User(BaseModel):
    """
    用户模型。
    """

    __tablename__ = "t_user"
    __table_args__ = {"comment": "用户表"}

    uid: Mapped[int] = mapped_column(BigInteger, unique=True, comment="用户uid，展示用")
    username: Mapped[str] = mapped_column(String(20), unique=True, comment="用户名")
    password: Mapped[str] = mapped_column(String(256), comment="密码")
    nickname: Mapped[str] = mapped_column(String(20), comment="昵称")
    gender: Mapped[int] = mapped_column(Integer, default=GenderEnum.SECRET.value, comment="性别(0:保密 1:男 2:女)")
    avatar: Mapped[str] = mapped_column(String(512), comment="个人头像")
    email: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, comment="邮箱")
    mobile: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, comment="手机号")
    wechat: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, comment="微信号")
    register_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="注册时间")
    last_login_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="最后登录时间")
    last_login_ip: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="最后登录IP")
    summary: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="个性签名")
    background: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="个人中心背景图")
    address: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="地址")
    is_official: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否是官方用户")


class UserRestriction(BaseModel):
    """
    用户限制模型。
    """

    __tablename__ = "t_user_restriction"
    __table_args__ = {"comment": "用户限制表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    restrict_type: Mapped[int] = mapped_column(Integer, comment="限制类型(1:封禁 2:禁言)")
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="限制开始时间")
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="限制结束时间")
    is_forever: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否永久限制")
    reason: Mapped[str] = mapped_column(String(1000), default="", comment="限制原因")
    is_cancel: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否解除")
    cancel_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="解除时间")
    cancel_reason: Mapped[str] = mapped_column(String(1000), default="", comment="解除原因")


class UserSettings(BaseModel):
    """
    用户设置模型。
    """

    __tablename__ = "t_user_settings"
    __table_args__ = {"comment": "用户设置表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    setting_key: Mapped[str] = mapped_column(String(100), comment="设置键")
    setting_value: Mapped[str] = mapped_column(String(1000), comment="设置值")


class Role(BaseModel):
    """
    角色模型。
    """

    __tablename__ = "t_role"
    __table_args__ = {"comment": "角色表"}

    code: Mapped[str] = mapped_column(String(20), unique=True, comment="角色标识")
    name: Mapped[str] = mapped_column(String(20), comment="角色名称")
    description: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="角色描述")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")


class UserRole(BaseModel):
    """
    用户角色模型。
    """

    __tablename__ = "t_user_role"
    __table_args__ = {"comment": "用户角色表"}

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户id")
    role_id: Mapped[int] = mapped_column(BigInteger, comment="角色id")


class Menu(BaseModel):
    """
    菜单模型。
    """

    __tablename__ = "t_menu"
    __table_args__ = {"comment": "菜单表"}

    parent_id: Mapped[int] = mapped_column(BigInteger, comment="所属上级")
    code: Mapped[str] = mapped_column(String(50), unique=True, comment="权限标识")
    name: Mapped[str] = mapped_column(String(20), comment="名称")
    menu_type: Mapped[int] = mapped_column(Integer, comment="类型(0:目录 1:菜单 2:按钮[权限])")
    route_name: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="路由名")
    path: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="路由地址")
    component: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="组件路径")
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="图标")
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否隐藏")
    always_show: Mapped[bool] = mapped_column(Boolean, default=False, comment="总是层级显示")
    is_out_link: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否是外链")
    index: Mapped[int] = mapped_column(Integer, default=100000, comment="排序(越小越在前)")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")


class RoleMenu(BaseModel):
    """
    角色菜单模型。
    """

    __tablename__ = "t_role_menu"
    __table_args__ = {"comment": "角色菜单表"}

    role_id: Mapped[int] = mapped_column(BigInteger, comment="角色id")
    menu_id: Mapped[int] = mapped_column(BigInteger, comment="权限(菜单)id")
