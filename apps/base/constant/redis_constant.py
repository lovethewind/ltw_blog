class RedisConstant:

    # 网站相关
    WEBSITE_VIEW_COUNT_KEY = "website_view_count"
    WEBSITE_VIEW_COUNT_THROTTLE_KEY = "website_view_count_throttle"

    # 防重复提交
    AVOID_REPEAT_SUBMIT_KEY = "avoid_repeat_submit"

    # 文章数量相关
    ARTICLE_VIEW_COUNT_ADD_WAIT_KEY = "article_view_count_add_wait"
    ARTICLE_VIEW_COUNT_MAP_KEY = "article_view_count_map"
    ARTICLE_PUBLISHED_VIEW_COUNT_ZSET_KEY = "article_published_view_count_zset"
    ARTICLE_LIKE_COUNT_MAP_KEY = "article_like_count_map"
    ARTICLE_COLLECT_COUNT_MAP_KEY = "article_collect_count_map"
    ARTICLE_COMMENT_COUNT_MAP_KEY = "article_comment_count_map"
    ARTICLE_PUBLISHED_LIST_KEY = "article_published_list"
    # 用户相关
    USER_UID_GENERATOR_KEY = "user_uid_generator"
    USER_UNBLOCK_KEY = "user_unblock"
    USER_ERROR_COUNT_KEY = "user_error_count"
    USER_LIKE_ARTICLE_ZSET_KEY = "user_like_article_zset"
    USER_LIKE_COMMENT_ZSET_KEY = "user_like_comment_zset"
    USER_COLLECT_ARTICLE_ZSET_KEY = "user_collect_article_zset"
    USER_FOLLOWER_SET_KEY = "user_follower_set"
    USER_FOLLOWER_COUNT_MAP_KEY = "user_follower_count_map"
    USER_FANS_COUNT_MAP_KEY = "user_fans_count_map"
    USER_VIEW_COUNT_MAP_KEY =  "user_view_count_map"

    # 评论相关
    COMMENT_LIKE_COUNT_MAP_KEY = "comment_like_count_map"

    # 验证码相关
    VERIFY_CODE_OP_KEY = "verify_code_op"

    # 微信登录
    WECHAT_CODE_OPENID_KEY = "wechat_code_openid"
    RANDOM_CODE_OPENID_KEY = "random_code_openid"

    # 图片点赞
    USER_LIKE_PICTURE_SET_KEY = "user_like_picture_set"
    PICTURE_LIKE_COUNT_MAP_KEY = "picture_like_count_map"
    PICTURE_LIKE_COUNT_ZSET_KEY = "picture_like_count_zset"

    # 分享点赞
    USER_LIKE_SHARE_SET_KEY = "user_like_share_set"
    SHARE_LIKE_COUNT_MAP_KEY = "share_like_count_map"

    # ES相关
    HOT_KEYWORDS_SEARCH_KEY = "hot_keywords_search"
    RECOMMEND_ARTICLE_SEARCH_KEY = "recommend_article_search"
    KEYWORDS_SEARCH_ARTICLE_CACHE_KEY = "keywords_search_article_cache"

    # 聊天相关
    CONVERSATION_UNREAD_COUNT_MAP_KEY = "conversation_unread_count_map"