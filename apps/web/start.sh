echo '启动项目'
cd "$(dirname "$0")/../.."
gunicorn -c apps/web/config.py apps.web.run:create_app
echo '项目启动成功'
