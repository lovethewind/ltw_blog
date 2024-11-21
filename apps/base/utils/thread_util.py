# @Time    : 2024/11/20 19:55
# @Author  : frank
# @File    : thread_util.py
from concurrent.futures import ThreadPoolExecutor

thread_pool = ThreadPoolExecutor(max_workers=50)