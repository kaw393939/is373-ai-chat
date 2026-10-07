"""Sanitized freshness derived from dump time, not the last download timestamp."""

import json
import re
from datetime import datetime, timezone

NAME = re.compile(r"daily-(\d{8}T\d{6}Z)\.tar\.age\Z")


def created(name):
    match = NAME.fullmatch(name)
    if not match:
        raise ValueError("Invalid encrypted backup timestamp")
    return datetime.strptime(match[1], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).timestamp()


def freshness(at, instant):
    return "ok" if 0 <= instant - at <= 36 * 3600 else "stale"


def backup_status(root, instant):
    local = {"status": "missing", "created_at": None}
    off_host = {**local, "received_at": None}
    try:
        dates = [
            created(path.name)
            for path in root.glob("daily-*.tar.age")
            if NAME.fullmatch(path.name) and not path.is_symlink() and path.stat().st_size
        ]
        if dates:
            at = max(dates)
            local = {"status": freshness(at, instant), "created_at": at}
        receipt = json.loads((root / "off-host-status.json").read_text())
        at = created(receipt["name"])
        received = datetime.fromisoformat(receipt["received_at"]).timestamp()
        off_host = {"status": freshness(at, instant), "created_at": at, "received_at": received}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return {"local": local, "off_host": off_host}
