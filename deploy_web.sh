echo "start deploy ltw-web"
git pull
docker build -t ltw-web:latest -f apps/web/Dockerfile .
docker rm -f ltw-web
docker run -d --name ltw-web --restart always --env-file .env \
  --memory=1g --network=ltw_blog -p 8001:8001 \
  ltw-web:latest