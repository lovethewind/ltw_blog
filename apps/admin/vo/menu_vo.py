from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminMenuCreateVO(BaseVO):
    """
    后台菜单创建参数。
    """

    parent_id: int = 0
    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=20)
    menu_type: int = Field(ge=0, le=2)
    route_name: str | None = Field(default=None, max_length=20)
    path: str | None = Field(default=None, max_length=50)
    component: str | None = Field(default=None, max_length=50)
    icon: str | None = Field(default=None, max_length=50)
    hidden: bool = False
    always_show: bool = False
    is_out_link: bool = False
    index: int = 100000
    is_active: bool = True

    @model_validator(mode="after")
    def validate_button_code(self) -> "AdminMenuCreateVO":
        """
        校验按钮菜单必须填写权限标识。

        :return: 当前菜单创建参数
        :raises ValueError: 按钮菜单缺少权限标识时抛出
        """
        if self.menu_type == 2 and not self.code:
            raise ValueError("按钮菜单必须填写权限标识")
        return self


class AdminMenuUpdateVO(BaseVO):
    """
    后台菜单更新参数。
    """

    parent_id: int | None = None
    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=20)
    menu_type: int | None = Field(default=None, ge=0, le=2)
    route_name: str | None = Field(default=None, max_length=20)
    path: str | None = Field(default=None, max_length=50)
    component: str | None = Field(default=None, max_length=50)
    icon: str | None = Field(default=None, max_length=50)
    hidden: bool | None = None
    always_show: bool | None = None
    is_out_link: bool | None = None
    index: int | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_button_code(self) -> "AdminMenuUpdateVO":
        """
        校验更新为按钮菜单时必须填写权限标识。

        :return: 当前菜单更新参数
        :raises ValueError: 更新为按钮菜单且缺少权限标识时抛出
        """
        if self.menu_type == 2 and not self.code:
            raise ValueError("按钮菜单必须填写权限标识")
        return self


class AdminRoleCreateVO(BaseVO):
    """
    后台角色创建参数。
    """

    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=128)
    is_active: bool = True


class AdminRoleUpdateVO(BaseVO):
    """
    后台角色更新参数。
    """

    code: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=128)
    is_active: bool | None = None


class AdminRoleMenuUpdateVO(BaseVO):
    """
    后台角色菜单授权参数。
    """

    menu_ids: list[int] = Field(default_factory=list)
