# @Time    : 2024/10/18 14:40
# @Author  : frank
# @File    : __init__.py.py
import sys

if sys.version_info >= (3, 12, 0):
    import six

    sys.modules['kafka.vendor.six.moves'] = six.moves
