from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminCategoryCreateVO(BaseVO):
    """
    后台分类创建参数。
    """

    name: str = Field(min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=1000)
    index: int = 100000
    is_active: bool = True


class AdminCategoryUpdateVO(BaseVO):
    """
    后台分类更新参数。
    """

    name: str | None = Field(default=None, min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=1000)
    index: int | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminCategoryUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 分类更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self
