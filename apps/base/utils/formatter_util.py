# @Time    : 2024/8/13 22:39
# @Author  : frank
# @File    : formatter_util.py


class FormatterUtil:
    @staticmethod
    def to_lower_camel(string: str) -> str:
        words = string.split('_')
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

    @staticmethod
    def to_upper_camel(string: str) -> str:
        words = string.split('_')
        return ''.join(word.capitalize() for word in words)

    @staticmethod
    def to_snake(string: str) -> str:
        return "".join(["_" + s.lower() if s.isupper() else s for s in string]).lstrip("_")


if __name__ == '__main__':
    print(FormatterUtil.to_lower_camel('hello_world'))
    print(FormatterUtil.to_upper_camel('hello_world'))
    print(FormatterUtil.to_snake('helloWorld'))
    print(FormatterUtil.to_snake('HelloWorld'))

