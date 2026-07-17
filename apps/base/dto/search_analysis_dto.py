from datetime import datetime

from pydantic import Field, field_validator

from apps.base.dto.base_dto import BaseDTO

DEFAULT_HOT_SEARCH_STOP_WORDS = ["一个", "什么", "如何", "怎么", "这个", "那个"]


class SearchAnalysisConfigDTO(BaseDTO):
    """搜索分词配置。"""

    custom_words: list[str] = Field(default_factory=list)
    stop_words: list[str] = Field(default_factory=list)
    hot_search_stop_words: list[str] = Field(default_factory=lambda: DEFAULT_HOT_SEARCH_STOP_WORDS.copy())
    version: int = Field(default=0, ge=0)
    published_at: datetime | None = None

    @field_validator("custom_words", "stop_words", "hot_search_stop_words", mode="before")
    @classmethod
    def normalize_words(cls, words: object) -> list[str]:
        """
        规范化词表，去除空白项和重复项。

        :param words: 原始词表。
        :return: 规范化后的词表。
        :raises ValueError: 词表格式、单词长度或数量不合法时抛出。
        """
        if words is None:
            return []
        if not isinstance(words, list):
            raise ValueError("词表必须是数组")
        result: list[str] = []
        seen: set[str] = set()
        for item in words:
            if not isinstance(item, str):
                raise ValueError("词表内容必须是字符串")
            word = item.strip()
            if not word:
                continue
            if "\n" in word or "\r" in word:
                raise ValueError("单个词不能包含换行")
            if len(word) > 50:
                raise ValueError("单个词不能超过 50 个字符")
            if word in seen:
                continue
            seen.add(word)
            result.append(word)
        if len(result) > 2000:
            raise ValueError("单个词表不能超过 2000 项")
        return result


class SearchAnalysisStateDTO(BaseDTO):
    """搜索分词配置状态。"""

    draft: SearchAnalysisConfigDTO
    published: SearchAnalysisConfigDTO
    history: list[SearchAnalysisConfigDTO] = Field(default_factory=list)


class SearchAnalysisPreviewDTO(BaseDTO):
    """搜索分词预览结果。"""

    tokens: list[str]
    filtered_tokens: list[str]


class SearchIndexRebuildDTO(BaseDTO):
    """文章搜索索引重建结果。"""

    index_name: str
    document_count: int
