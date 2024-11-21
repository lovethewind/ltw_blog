cd apps/web
echo '安装依赖包'
pip3 install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
echo '启动项目'
gunicorn -c config.py run:create_app
echo '项目启动成功'