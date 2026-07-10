#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "start deploy ltw-admin"

git config pull.rebase false 2>/dev/null || true
git pull
docker build -t ltw-admin:latest -f apps/admin/Dockerfile .
docker rm -f ltw-admin
docker run -d --name ltw-admin --restart always --env-file .env \
  --memory=1g --network=ltw_blog -p 8002:8002 \
  ltw-admin:latest
