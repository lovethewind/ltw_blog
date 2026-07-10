from pydantic import Field

from apps.admin.dto.base_dto import BaseDTO


class AdminMenuDTO(BaseDTO):
    """
    后台菜单 DTO。
    """

    id: int
    parent_id: int
    code: str | None = None
    name: str
    menu_type: int
    route_name: str | None = None
    path: str | None = None
    component: str | None = None
    icon: str | None = None
    hidden: bool
    always_show: bool
    is_out_link: bool
    index: int
    is_active: bool
    children: list["AdminMenuDTO"] = Field(default_factory=list)


class AdminRoleDTO(BaseDTO):
    """
    后台角色 DTO。
    """

    id: int
    code: str
    name: str
    description: str | None = None
    is_active: bool
