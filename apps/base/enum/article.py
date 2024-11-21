from enum import IntEnum


class ArticleStatusEnum(IntEnum):
    """
    文章状态 1:草稿 2:已发布 3:待审核 4:回收站
    """
    DRAFT = 1
    PUBLISHED = 2
    CHECKING = 3
    DELETED = 4

if __name__ == '__main__':
    print(ArticleStatusEnum.__dict__["_member_map_"].values())