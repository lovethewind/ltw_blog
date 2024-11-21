from jose import jwt
from jose.constants import ALGORITHMS


class TokenUtil:
    secret_key = "nAm1aVIe"
    algorithm = ALGORITHMS.HS256

    @classmethod
    def create_token(cls, user_id: int, username: str):
        payload = {"username": username, "user_id": user_id}
        token = jwt.encode(payload, key=cls.secret_key, algorithm=cls.algorithm)
        return token

    @classmethod
    def get_user_id(cls, token: str):
        payload = jwt.decode(token, key=cls.secret_key)
        return payload.get("user_id")

    @classmethod
    def get_username(cls, token: str):
        payload = jwt.decode(token, key=cls.secret_key)
        return payload.get("username")


if __name__ == '__main__':
    import string
    import random

    pwd = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    print(pwd)

    print(TokenUtil.create_token(1, "frank"))
