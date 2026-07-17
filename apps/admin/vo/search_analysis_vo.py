from pydantic import Field

from apps.admin.vo.base_vo import BaseVO
from apps.base.dto.search_analysis_dto import DEFAULT_HOT_SEARCH_STOP_WORDS, SearchAnalysisConfigDTO


class SearchAnalysisConfigVO(BaseVO):
    """搜索分词草稿参数。"""

    custom_words: list[str] = Field(default_factory=list)
    stop_words: list[str] = Field(default_factory=list)
    hot_search_stop_words: list[str] = Field(default_factory=lambda: DEFAULT_HOT_SEARCH_STOP_WORDS.copy())

    def to_dto(self) -> SearchAnalysisConfigDTO:
        """
        转换为规范化后的搜索配置 DTO。

        :return: 搜索配置 DTO。
        """
        return SearchAnalysisConfigDTO.model_validate(self.model_dump())


class SearchAnalysisPreviewVO(BaseVO):
    """搜索分词预览参数。"""

    text: str = Field(min_length=1, max_length=500)
    stop_words: list[str] = Field(default_factory=list)
