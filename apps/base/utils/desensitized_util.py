class DesensitizedUtil:
    """
    脱敏工具
    """

    @classmethod
    def mobile_phone(cls, num: str):
        """
        手机号脱敏
        """
        if not num:
            return num
        return cls._replace(num, start_include=3, end_exclude=len(num) - 4)

    @classmethod
    def email(cls, email: str):
        """
        邮箱脱敏
        """
        if not email:
            return email
        return cls._replace(email, start_include=1, end_exclude=email.index("@"))

    @classmethod
    def password(cls, password: str):
        """
        全字符加密通用
        """
        if not password:
            return password
        return "*" * len(password)

    @classmethod
    def _replace(cls, text, start_include: int, end_exclude: int, replaced_char="*"):
        """
        替换字符串
        """
        if not text:
            return text
        if start_include > end_exclude:
            return text
        return text[:start_include] + replaced_char * (end_exclude - start_include) + text[end_exclude:]


if __name__ == '__main__':
    print(DesensitizedUtil.mobile_phone("13202012323"))
    print(DesensitizedUtil.email("1237373@qq.com"))
    print(DesensitizedUtil.password("1237373@qq.com"))
