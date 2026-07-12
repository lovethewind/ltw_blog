from pydantic import Field, model_validator

from apps.admin.vo.base_vo import BaseVO


class AdminWebsiteCategoryCreateVO(BaseVO):
    """
    后台网站导航分类创建参数。
    """

    name: str = Field(min_length=1, max_length=100)
    index: int = 100000


class AdminWebsiteCategoryUpdateVO(BaseVO):
    """
    后台网站导航分类更新参数。
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    index: int | None = None

    @model_validator(mode="after")
    def ensure_update_field(self) -> "AdminWebsiteCategoryUpdateVO":
        """
        校验至少包含一个更新字段。

        :return: 网站导航分类更新参数
        :raises ValueError: 没有更新字段时抛出
        """
        if not self.model_dump(exclude_none=True):
            raise ValueError("请至少填写一个更新字段")
        return self
