import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

loader = SourceFileLoader(
    "backup_export", str(Path(__file__).parents[2] / "deploy/chat-backup-export")
)
spec = importlib.util.spec_from_loader(loader.name, loader)
export = importlib.util.module_from_spec(spec)
loader.exec_module(export)


@pytest.mark.parametrize(
    "name", ["../.env", "daily-20261007.dump", "daily-20261007T000000Z.tar.age.sha256", ""]
)
def test_export_never_accepts_plaintext_or_path_arguments(name):
    with pytest.raises(ValueError):
        export.checked(name)


def test_export_does_not_follow_archive_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr(export, "ROOT", tmp_path)
    private = tmp_path / ".env"
    private.write_text("SYNTHETIC=never-export")
    (tmp_path / "daily-20261007T000000Z.tar.age").symlink_to(private)
    with pytest.raises(ValueError):
        export.checked("daily-20261007T000000Z.tar.age")


def test_wrong_receipt_cannot_make_off_host_status_fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(export, "ROOT", tmp_path)
    name = "daily-20261007T000000Z.tar.age"
    (tmp_path / name).write_bytes(b"synthetic encrypted bytes")
    with pytest.raises(ValueError):
        export.execute(["ack", name, "0" * 64])
    assert not (tmp_path / "off-host-status.json").exists()


def test_correct_receipt_is_private_and_checked(tmp_path, monkeypatch):
    monkeypatch.setattr(export, "ROOT", tmp_path)
    name = "daily-20261007T000000Z.tar.age"
    path = tmp_path / name
    path.write_bytes(b"synthetic encrypted bytes")
    export.execute(["ack", name, export.metadata(path)["sha256"]])
    assert (tmp_path / "off-host-status.json").stat().st_mode & 0o777 == 0o600
