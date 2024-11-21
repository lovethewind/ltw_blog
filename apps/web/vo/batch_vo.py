# @Time    : 2024/9/4 10:09
# @Author  : frank
# @File    : batch_vo.py
from apps.web.vo.base_vo import BaseVO


class BatchVO(BaseVO):
    ids: list[int]
