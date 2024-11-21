#!/usr/bin/env bash
project=ltw_web
docker_path=/data/app
version=0.0.1
env=${1:-test}
echo "will deploy ${project}:${version}"

echo "git pull"
#git pull

echo "start docker build"
docker build -f Dockerfile -t lovethewind/${project}:${version} .
docker stop ${project}
docker rm -f ${project}

echo "start docker run"
docker run -d --name ${project} --restart always \
 -p 8001:8001 \
 --network=ltw_blog \
 -e TZ="Asia/Shanghai" -e APP_ACTIVE=${env} \
 -v /Users/goujincheng/Documents/Docker/${project}:${docker_path} lovethewind/${project}:${version}