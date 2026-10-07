"""Bounded encrypted transfers: interrupted/corrupt copies cannot become recoverable backups."""

import hashlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "backup_vault", Path(__file__).parents[2] / "scripts/backup-vault.py"
)
vault = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vault)
NAME = "daily-20261007T000000Z.tar.age"
CONTENT = b"synthetic encrypted bytes"
VALUE = {"name": NAME, "bytes": len(CONTENT), "sha256": hashlib.sha256(CONTENT).hexdigest()}


class Export:
    def __init__(self, content=CONTENT, fail=False):
        self.commands, self.content, self.fail = [], content, fail

    def __call__(self, command, **kwargs):
        self.commands.append(command[-1])
        if command[-1] == "list":
            return subprocess.CompletedProcess(command, 0, json.dumps([VALUE]).encode())
        if command[-1].startswith("fetch "):
            kwargs["stdout"].write(self.content)
            if self.fail:
                raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0, b"")


def test_valid_transfer_is_private_verified_and_reused(tmp_path):
    destination, export = tmp_path / "vault", Export()
    receipt = vault.pull(["synthetic-ssh"], destination, export)
    assert receipt["sha256"] == VALUE["sha256"]
    assert (destination / NAME).stat().st_mode & 0o777 == 0o600
    assert (destination / "receipt.json").stat().st_mode & 0o777 == 0o600
    assert destination.stat().st_mode & 0o777 == 0o700
    vault.pull(["synthetic-ssh"], destination, export)
    assert len([command for command in export.commands if command.startswith("fetch ")]) == 1
    assert (
        vault.status(destination, datetime(2026, 10, 7, 12, tzinfo=timezone.utc))["age_hours"] == 12
    )


@pytest.mark.parametrize("export", [Export(b"corrupt"), Export(CONTENT, fail=True)])
def test_failed_transfer_is_not_acknowledged_or_published(tmp_path, export):
    destination = tmp_path / "vault"
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        vault.pull(["synthetic-ssh"], destination, export)
    assert not list(destination.iterdir())
    assert not any(command.startswith("ack ") for command in export.commands)


@pytest.mark.parametrize(
    "value",
    [
        {**VALUE, "name": "../.env"},
        {**VALUE, "bytes": 0},
        {**VALUE, "bytes": vault.MAX_BYTES + 1},
        {**VALUE, "sha256": "malformed"},
    ],
)
def test_untrusted_inventory_rejected(value):
    with pytest.raises(ValueError):
        vault.validate_list([value])


def test_fresh_receipt_cannot_hide_stale_backup(tmp_path):
    vault.pull(["synthetic-ssh"], tmp_path / "vault", Export())
    with pytest.raises(ValueError, match="older than"):
        vault.status(tmp_path / "vault", datetime(2026, 10, 9, tzinfo=timezone.utc))


def test_vault_symlink_is_rejected_without_transfer(tmp_path):
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    destination = tmp_path / "vault"
    destination.symlink_to(real, target_is_directory=True)
    export = Export()
    with pytest.raises(ValueError):
        vault.pull(["synthetic-ssh"], destination, export)
    assert export.commands == []


def test_ssh_requires_pinned_host_and_private_key(tmp_path):
    key, known = tmp_path / "key", tmp_path / "known"
    key.write_text("synthetic key")
    known.write_text("synthetic host pin")
    with pytest.raises(ValueError):
        vault.ssh_command("operator@example.org", key, known)
    key.chmod(0o600)
    command = vault.ssh_command("operator@example.org", key, known)
    assert "StrictHostKeyChecking=yes" in command and "IdentitiesOnly=yes" in command
    with pytest.raises(ValueError):
        vault.ssh_command("operator@example.org;cat .env", key, known)
