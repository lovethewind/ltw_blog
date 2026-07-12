echo '启动定时任务服务'
cd "$(dirname "$0")/../.."
python -m apps.scheduler.run
