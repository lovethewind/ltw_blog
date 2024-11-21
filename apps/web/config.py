# @Time    : 2024/11/20 22:10
# @Author  : frank
# @File    : config.py
# -*- coding:utf-8 _*-
import multiprocessing

bind = '0.0.0.0:8001'  # 指定监听的地址和端口，用于nginx转发
backlog = 2048  # 服务器中排队等待的最大连接数，建议值64-2048，超过2048时client连接会得到一个error。

workers = multiprocessing.cpu_count() * 2 + 1  # 用于处理工作的进程数，这里使用了文档建议的值
worker_class = 'uvicorn.workers.UvicornWorker'  # worker进程的工作方式，有sync、eventlet、gevent、tornado、gthread, 缺省值sync, django使用gthread的方式好一些。
worker_connections = 1000  # 最大客户端并发数量，默认情况下这个值为1000。此设置将影响gevent和eventlet工作模式

threads = int(480 / workers)  # 数据库连接数=workers*threads*2
timeout = 60  # 访问超时时间，默认30s
graceful_timeout = 60  # 接收到restart信号后，worker可以在graceful_timeout时间内，继续处理完当前requests。
keepalive = 2  # server端保持连接时间，默认情况下值为2。一般设定在1~5秒之间。
limit_request_line = 4094  # HTTP请求行的最大大小，默认值为4094。范围是0~8190,此参数可以防止任何DDOS攻击
limit_request_fields = 100  # 限制HTTP请求中请求头字段的数量,默认值为100，范围是0~32768,此参数可以防止任何DDOS攻击
limit_request_field_size = 8190  # 限制HTTP请求中请求头的大小，默认值为8190

reload = False  # 代码更新时不重启项目
daemon = False  # Gunicorn是否为守护进程（后端进程），默认为False
# max_requests = 1000  # 有内存泄露时使用此选项重启work
# max_requests_jitter = 50  # 重启work的抖动幅度，一般设置为max_requests的5%
pidfile = './gunicorn.pid'  # pid文件的文件名

# keyfile = '.../server.key'  # ssl证书密钥文件路径
# certfile = '.../server.crt'  # ssl证书文件路径

accesslog = '-'  # 访问日志文件路径，'-'表示输出到终端
access_log_format = '%(t)s %(h)s "%(r)s" %(s)s %(b)s "%(f)s" "%(L)s"'  # 访问日志文件格式

errorlog = '-'  # 错误日志文件路径，'-'表示输出到终端
# loglevel = '-'  # 错误级别，debug(调试)、info(信息)、warning(警告)、error(错误)、critical(危急)

# pythonpath = '/home/ubuntu/anaconda3/bin/python -u'  # 逗号分隔的Python执行路径，可以加上参数，这里只有一个路径，-u表示使用无缓冲的二进制终端输出流
# project_name = 'Discern'
# proc_name = 'gunicorn_%s' % project_name  # 设置进程名称
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', '%s.settings' % project_name)  # 设置环境变量指定Django运行使用的配置文件
# os.environ.setdefault('WERKZEUG_RUN_MAIN', 'true')  # 设置环境变量告诉wekzeug这个是用于reload的主进程
