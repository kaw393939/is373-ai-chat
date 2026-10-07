import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "backup_status", Path(__file__).parents[2] / "deploy/backup_status.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
INSTANT = datetime(2026, 10, 7, 12, tzinfo=timezone.utc).timestamp()
NAME = "daily-20261007T000000Z.tar.age"


def test_missing_and_empty_archives_do_not_report_success(tmp_path):
    (tmp_path / NAME).touch()
    value = module.backup_status(tmp_path, INSTANT)
    assert value["local"]["status"] == "missing"
    assert value["off_host"]["status"] == "missing"


def test_backup_dates_and_receipts_are_sanitized(tmp_path):
    (tmp_path / NAME).write_bytes(b"ciphertext")
    (tmp_path / "off-host-status.json").write_text(
        json.dumps(
            {
                "name": NAME,
                "received_at": "2026-10-07T11:00:00+00:00",
                "extra": "never-shared",
            }
        )
    )
    value = module.backup_status(tmp_path, INSTANT)
    assert value["local"]["status"] == value["off_host"]["status"] == "ok"
    assert "never-shared" not in json.dumps(value) and "daily-" not in json.dumps(value)
    assert module.backup_status(tmp_path, INSTANT + 36 * 3600)["off_host"]["status"] == "stale"


def test_recent_receipt_for_old_dump_stays_stale(tmp_path):
    (tmp_path / "off-host-status.json").write_text(
        json.dumps(
            {
                "name": "daily-20260901T000000Z.tar.age",
                "received_at": "2026-10-07T11:00:00+00:00",
            }
        )
    )
    assert module.backup_status(tmp_path, INSTANT)["off_host"]["status"] == "stale"


def test_corrupt_receipt_does_not_hide_valid_local_archive(tmp_path):
    (tmp_path / NAME).write_bytes(b"ciphertext")
    (tmp_path / "off-host-status.json").write_text("not-json")
    value = module.backup_status(tmp_path, INSTANT)
    assert value["local"]["status"] == "ok" and value["off_host"]["status"] == "missing"
