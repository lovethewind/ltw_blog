echo '启动项目'
cd "$(dirname "$0")/../.."
rm -f gunicorn.pid && gunicorn "apps.web.run:create_app()" -c apps/web/gunicorn_config.py
echo '项目启动成功'
