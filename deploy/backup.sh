#!/bin/bash
# Only the recovery computer has the age identity. This host gets its public recipient.
set -euo pipefail
umask 077
cd /opt/is373-ai-chat
# A dump and its schema/config/image inventory must describe one release.
# Serialize with the deployer before reading any of those identities.
mkdir -p /var/lib/chat-release
chmod 700 /var/lib/chat-release
exec 8>/var/lib/chat-release/deploy.lock
flock 8
exec 9>/run/lock/chat-backup.lock
flock -n 9 || exit 0
export APP_IMAGE="$(cat current-image)"
test -s /etc/chat-backup/recipients.txt
command -v age >/dev/null
mkdir -p backups
chmod 700 backups
work="$(mktemp -d backups/.work-XXXXXXXX)"
partial=""
trap 'rm -rf -- "$work"; test -z "$partial" || rm -f -- "$partial"' EXIT
docker compose exec -T db pg_dump -U chat -d chat -Fc > "$work/database.dump"
test -s "$work/database.dump"
schema="$(docker compose exec -T db psql -U chat -d chat -Atc 'SELECT version_num FROM alembic_version')"
test -n "$schema"
cp -- .env compose.yaml current-image "$work/"
test ! -f release.json || cp -- release.json "$work/"
python3 - "$work" "$schema" <<'PY'
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
path = Path(sys.argv[1])
def checksum(file):
    with file.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
manifest = {"format": 1, "created_at": datetime.now(timezone.utc).isoformat(),
            "schema": sys.argv[2], "image": (path / "current-image").read_text().strip(),
            "files": {p.name: checksum(p)
                      for p in path.iterdir() if p.is_file()}}
(path / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
PY
name="daily-$(date -u +%Y%m%dT%H%M%SZ).tar.age"
partial="backups/.$name.partial"
tar -C "$work" -cf - . | age -R /etc/chat-backup/recipients.txt -o "$partial"
test -s "$partial"
test ! -e "backups/$name"
mv -- "$partial" "backups/$name"
partial=""
sha256sum "backups/$name" > "backups/$name.sha256"
# Existing plaintext deployment snapshots require explicit cleanup after a verified restore.
find backups -maxdepth 1 -type f -name 'daily-????????T??????Z.tar.age*' -mtime +14 -delete
docker compose run --rm --no-deps app python -m app.cli prune
printf 'Encrypted chat backup created: %s\n' "$name"
