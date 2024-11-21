from tortoise import fields

from apps.base.enum.user import GenderEnum, UserTagEnum, MenuTypeEnum, UserRestrictionTypeEnum, UserSettingsEnum
from apps.base.models.base import BaseModel


class User(BaseModel):
    uid = fields.BigIntField(unique=True, description="用户uid，展示用")
    username = fields.CharField(max_length=20, unique=True, description="用户名")
    password = fields.CharField(max_length=256, description="密码")
    nickname = fields.CharField(max_length=20, description="昵称")
    gender = fields.IntEnumField(GenderEnum, default=GenderEnum.SECRET.value, description="性别(0:保密 1:男 2:女)")
    avatar = fields.CharField(max_length=512, description="个人头像")
    email = fields.CharField(max_length=128, unique=True, null=True, description="邮箱")
    mobile = fields.CharField(max_length=20, unique=True, null=True, description="手机号")
    wechat = fields.CharField(max_length=128, unique=True, null=True, description="微信号")
    register_time = fields.DatetimeField(auto_now_add=True, description="注册时间")
    last_login_time = fields.DatetimeField(null=True, description="最后登录时间")
    last_login_ip = fields.CharField(max_length=20, null=True, description="最后登录IP")
    occupation = fields.CharField(max_length=20, null=True, description="职业(头衔)")
    summary = fields.CharField(max_length=100, null=True, description="个性签名")
    background = fields.CharField(max_length=512, null=True, description="个人中心背景图")
    address = fields.CharField(max_length=100, null=True, description="地址")
    is_official = fields.BooleanField(default=False, description="是否是官方用户")
    user_tag = fields.IntEnumField(UserTagEnum, default=UserTagEnum.NORMAL_USER.value,
                                   description="用户标签(0:超级管理员 1:管理员 2:普通用户 3:其他)")

    class Meta:
        table = "t_user"
        table_description = "用户表"


class UserRestriction(BaseModel):
    user_id = fields.BigIntField(description="用户id")
    restrict_type = fields.IntEnumField(UserRestrictionTypeEnum, description="限制类型(1:封禁 2:禁言)")
    start_time = fields.DatetimeField(null=True, description="限制开始时间")
    end_time = fields.DatetimeField(null=True, description="限制结束时间")
    is_forever = fields.BooleanField(default=False, description="是否永久限制")
    reason = fields.CharField(max_length=1000, default='', description="限制原因")
    is_cancel = fields.BooleanField(default=False, description="是否解除")
    cancel_time = fields.DatetimeField(null=True, description="解除时间")
    cancel_reason = fields.CharField(max_length=1000, default='', description="解除原因")

    class Meta:
        table = "t_user_restriction"
        table_description = "用户限制表"


class UserSettings(BaseModel):
    user_id = fields.BigIntField(description="用户id")
    setting_key = fields.CharEnumField(UserSettingsEnum, description="设置键")
    setting_value = fields.CharField(max_length=1000, description="设置值")

    class Meta:
        table = "t_user_settings"
        table_description = "用户设置表"


class Role(BaseModel):
    code = fields.CharField(max_length=20, unique=True, description="角色标识")
    name = fields.CharField(max_length=20, description="角色名称")
    description = fields.CharField(max_length=128, null=True, description="角色描述")
    is_active = fields.BooleanField(default=True, description="是否激活")

    class Meta:
        table = "t_role"
        table_description = "角色表"


class UserRole(BaseModel):
    user_id = fields.BigIntField(description="用户id")
    role_id = fields.BigIntField(description="角色id")

    class Meta:
        table = "t_user_role"
        table_description = "用户角色表"


class Menu(BaseModel):
    parent_id = fields.BigIntField(description="所属上级")
    code = fields.CharField(max_length=50, unique=True, description="权限标识")
    name = fields.CharField(max_length=20, description="名称")
    menu_type = fields.IntEnumField(MenuTypeEnum, description="类型(0:目录 1:菜单 2:按钮[权限])")
    route_name = fields.CharField(max_length=20, null=True, description="路由名")
    path = fields.CharField(max_length=50, null=True, description="路由地址")
    component = fields.CharField(max_length=50, null=True, description="组件路径")
    icon = fields.CharField(max_length=50, null=True, description="图标")
    hidden = fields.BooleanField(default=False, description="是否隐藏")
    always_show = fields.BooleanField(default=False, description="总是层级显示")
    is_out_link = fields.BooleanField(default=False, description="是否是外链")
    index = fields.IntField(default=100000, description="排序(越小越在前)")
    is_active = fields.BooleanField(default=True, description="是否激活")

    class Meta:
        table = "t_menu"
        table_description = "菜单表"


class RoleMenu(BaseModel):
    role_id = fields.BigIntField(description="角色id")
    menu_id = fields.BigIntField(description="权限(菜单)id")

    class Meta:
        table = "t_role_menu"
        table_description = "角色菜单表"
