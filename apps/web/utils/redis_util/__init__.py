from typing import Any

from apps.base.core.depend_inject import Component, RefreshScope
from apps.base.utils.redis_util import RedisUtil as BaseRedisUtil

from .action import ActionMethod
from .article import ArticleMethod
from .chat import ChatMethod
from .comment import CommentMethod
from .es import ESMethod
from .picture import PictureMethod
from .user import UserMethod
from .verify_code import VerifyCodeMethod
from .website import WebsiteMethod
from .wechat import WechatMethod


@Component("webRedisUtil")
@RefreshScope("redis")
class WebRedisUtil(BaseRedisUtil):
    """
    web 业务 Redis 聚合工具。
    """

    def __init__(self) -> None:
        """
        初始化 web 业务 Redis 方法。

        :return: None。
        """
        super().__init__()
        self.Article: ArticleMethod = ArticleMethod(self.redis)
        self.Action: ActionMethod = ActionMethod(self.redis)
        self.VerifyCode: VerifyCodeMethod = VerifyCodeMethod(self.redis)
        self.User: UserMethod = UserMethod(self.redis)
        self.Wechat: WechatMethod = WechatMethod(self.redis)
        self.Comment: CommentMethod = CommentMethod(self.redis)
        self.Website: WebsiteMethod = WebsiteMethod(self.redis)
        self.ES: ESMethod = ESMethod(self.redis)
        self.Picture: PictureMethod = PictureMethod(self.redis)
        self.Chat: ChatMethod = ChatMethod(self.redis)

    async def get(self, key: str) -> Any:
        """
        获取 Redis 字符串值。

        :param key: Redis key。
        :return: Redis 值。
        """
        return await super().get(key)


__all__ = ["WebRedisUtil"]
