#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "start deploy ltw-web"

git config pull.rebase false 2>/dev/null || true
git pull
docker build -t ltw-web:latest -f apps/web/Dockerfile .
docker rm -f ltw-web
docker run -d --name ltw-web --restart always --env-file .env \
  --memory=1g --network=ltw_blog -p 8001:8001 \
  ltw-web:latest