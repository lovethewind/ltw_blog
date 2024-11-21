import bcrypt


class EncryptUtil:

    @classmethod
    def encrypt(cls, text: str):
        encrypt_text = bcrypt.hashpw(text.encode("utf-8"), bcrypt.gensalt())
        return encrypt_text.decode("utf-8")

    @classmethod
    def equals(cls, text: str, encrypt_text: str):
        return bcrypt.checkpw(text.encode("utf-8"), encrypt_text.encode("utf-8"))


if __name__ == '__main__':
    print(EncryptUtil.encrypt("nacoss1"))
