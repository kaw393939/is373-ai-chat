#!/bin/sh
# Local dumps supplement an off-host backup; configure that destination separately.
set -eu
cd /opt/is373-ai-chat
export APP_IMAGE="$(cat current-image)"
mkdir -p backups
chmod 700 backups
umask 077
docker compose exec -T db pg_dump -U chat -d chat -Fc > "backups/daily-$(date -u +%Y%m%d).dump"
# Remove only this script's daily dump pattern after 14 days.
find backups -name 'daily-*.dump' -type f -mtime +14 -delete
docker compose run --rm --no-deps app python -m app.cli prune
