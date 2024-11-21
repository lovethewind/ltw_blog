# @Time    : 2024/10/17 17:41
# @Author  : frank
# @File    : random_util.py
import random
import string
import uuid


class RandomUtil:

    @classmethod
    def random_numbers(cls, length: int = 6) -> str:
        """
        生成随机数字
        :param length: 长度
        :return:
        """
        return "".join(random.sample(string.digits, length))

    @classmethod
    def uuid4(cls):
        """
        生成随机uuid
        :return:
        """
        return uuid.uuid4().hex
