#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "start deploy ltw-scheduler"

git config pull.rebase false 2>/dev/null || true
git pull
docker build -t ltw-scheduler:latest -f apps/scheduler/Dockerfile .
docker rm -f ltw-scheduler
docker run -d --name ltw-scheduler --restart always --env-file .env \
  --memory=512m --network=ltw_blog \
  ltw-scheduler:latest