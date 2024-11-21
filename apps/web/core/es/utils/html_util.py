# @Time    : 2024/10/15 14:11
# @Author  : frank
# @File    : html_util.py
import re


class HtmlUtil:

    @classmethod
    def remove_html_tags(cls, text):
        text = text.replace("\n", " ")
        # 定义HTML标签的正则表达式
        tag_re = re.compile(r'<[^>]+>')
        # 使用sub方法替换掉所有匹配到的HTML标签
        return tag_re.sub('', text)