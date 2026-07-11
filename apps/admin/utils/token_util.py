from jose import jwt
from jose.constants import ALGORITHMS


class AdminTokenUtil:
    """
    后台管理 Token 工具。
    """

    secret_key = "nAm1aVIe"
    algorithm = ALGORITHMS.HS256

    @classmethod
    def create_token(cls, user_id: int, username: str) -> str:
        """
        创建后台管理用户 Token。

        :param user_id: 用户 ID。
        :param username: 用户名。
        :return: JWT Token。
        """
        payload = {"username": username, "user_id": user_id}
        token = jwt.encode(payload, key=cls.secret_key, algorithm=cls.algorithm)
        return token

    @classmethod
    def get_user_id(cls, token: str) -> int | None:
        """
        从 Token 中解析用户 ID。

        :param token: JWT Token。
        :return: 用户 ID。
        """
        payload = jwt.decode(token, key=cls.secret_key)
        return payload.get("user_id")

    @classmethod
    def get_username(cls, token: str) -> str | None:
        """
        从 Token 中解析用户名。

        :param token: JWT Token。
        :return: 用户名。
        """
        payload = jwt.decode(token, key=cls.secret_key)
        return payload.get("username")
