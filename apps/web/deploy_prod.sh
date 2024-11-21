#!/usr/bin/env bash
project=ltw_web
docker_path=/data/app
version=0.0.1
env=${1:-prod}
echo "will deploy ${project}:${version}"

echo "git pull"
git pull

echo "start docker build"
docker build -f Dockerfile -t lovethewind/${project}:${version} .
docker stop ${project}
docker rm -f ${project}

echo "start docker run"
docker run -d --name ${project} --restart always --network=host \
 -e TZ="Asia/Shanghai" -e APP_ACTIVE=${env} \
 -v /data/ltw_blog:${docker_path} lovethewind/${project}:${version}