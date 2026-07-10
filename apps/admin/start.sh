echo '启动项目'
cd "$(dirname "$0")/../.."
rm -f gunicorn.pid && gunicorn "apps.admin.run:create_app()" -c apps/admin/gunicorn_config.py
echo '项目启动成功'
