"""Fault injection proves failed staging cannot silently promote a candidate."""

import importlib.util
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

loader = SourceFileLoader("chat_deploy", str(Path(__file__).parents[2] / "deploy/chat-deploy"))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)


@pytest.fixture
def installed(tmp_path):
    (tmp_path / ".env").write_text("SYNTHETIC=true\n")
    (tmp_path / ".env").chmod(0o600)
    (tmp_path / "compose.yaml").write_bytes(b"old compose")
    (tmp_path / "current-image").write_bytes(b"old image\n")
    (tmp_path / "release.json").write_bytes(b'{"status":"deployed","commit":"old"}')
    return tmp_path


class Docker:
    def __init__(self, failure=None):
        self.failure, self.commands, self.revision, self.failed = failure, [], "0002", False

    def __call__(self, args, **kwargs):
        self.commands.append(args)
        if args[:2] == ["docker", "create"]:
            return b"probe"
        if args[:2] == ["docker", "cp"]:
            Path(args[-1]).write_bytes(b"candidate compose")
        operation = None
        if "--quiet" in args:
            operation = "config"
        elif "up" in args and args[-1] == "db":
            operation = "database"
        elif "pg_dump" in args:
            operation = "backup"
        elif "alembic" in args:
            operation = "migration"
            if self.failure == "changed-schema":
                self.revision = "0003"
                raise RuntimeError("synthetic migration failure")
        if operation is not None and operation == self.failure and not self.failed:
            self.failed = True
            raise RuntimeError("synthetic failure")
        if args[-1] == "SELECT to_regclass('public.alembic_version')":
            return b"alembic_version"
        if args[-1] == "SELECT version_num FROM alembic_version":
            return self.revision.encode()
        if "pg_dump" in args:
            return b"synthetic custom-format dump"
        if "python" in args and "-c" in args:
            return json.dumps(
                {
                    "commit": "candidate",
                    "schema": self.revision,
                    "version": "2.0.0",
                    "provider": "mock",
                }
            ).encode()
        return b""


@pytest.mark.parametrize("failure", ["config", "database", "backup", "migration"])
def test_failed_candidate_preserves_active_release(installed, failure):
    original = {
        name: (installed / name).read_bytes()
        for name in ["compose.yaml", "current-image", "release.json"]
    }
    docker = Docker(failure)
    with pytest.raises(RuntimeError, match="Deployment failed"):
        module.deploy(installed, "candidate image", "candidate", docker, {})
    assert original == {name: (installed / name).read_bytes() for name in original}
    attempt = json.loads((installed / "last-attempt.json").read_text())
    assert attempt["status"] == "failed"
    assert (
        not any("alembic" in args for args in docker.commands)
        if failure in {"config", "database", "backup"}
        else True
    )
    if failure == "config":
        assert not any("up" in args for args in docker.commands)


def test_schema_change_failure_stops_app_without_downgrade(installed):
    docker = Docker("changed-schema")
    with pytest.raises(RuntimeError, match="operator-required"):
        module.deploy(installed, "candidate image", "candidate", docker, {})
    assert json.loads((installed / "last-attempt.json").read_text())["schema_after"] == "0003"
    assert any(args[-2:] == ["stop", "app"] for args in docker.commands)
    assert not any("downgrade" in args for args in docker.commands)
    assert json.loads((installed / "release.json").read_text())["status"] != "deployed"


def test_success_records_identity_and_private_nonempty_backup(installed):
    record = module.deploy(installed, "candidate image", "candidate", Docker(), {})
    assert record["status"] == "deployed"
    assert (installed / "compose.yaml").read_bytes() == b"candidate compose"
    assert json.loads((installed / "release.json").read_text()) == record
    dump = next((installed / "backups").glob("*.dump"))
    assert dump.stat().st_mode & 0o777 == 0o600 and dump.stat().st_size


def test_empty_backup_does_not_migrate_or_promote(installed):
    docker = Docker()

    def empty(args, **kwargs):
        value = docker(args, **kwargs)
        return b"" if "pg_dump" in args else value

    with pytest.raises(RuntimeError, match="backup"):
        module.deploy(installed, "candidate image", "candidate", empty, {})
    assert not any("alembic" in args for args in docker.commands)
    assert (installed / "compose.yaml").read_bytes() == b"old compose"
    assert not list((installed / "backups").glob("*.dump"))


def test_preview_extracts_its_own_model_and_records_schema_boundary(installed):
    docker = Docker()
    record = module.deploy(installed, "candidate image", "candidate", docker, {}, "2.0.0", "qa")
    assert any(
        args[2] == "probe:/app/deploy/compose.preview.yaml"
        for args in docker.commands
        if args[:2] == ["docker", "cp"]
    )
    assert record["environment"] == "qa" and record["version"] == "2.0.0"
    assert record["schema"] == record["previous_schema"] == "0002"


def test_required_protected_configuration_precedes_any_docker_operation(installed):
    (installed / ".env").chmod(0o644)
    docker = Docker()
    with pytest.raises(ValueError, match="0600"):
        module.deploy(installed, "image", "commit", docker, {})
    assert docker.commands == []


def test_failed_recovery_cannot_leave_a_deployed_status(installed):
    docker = Docker("backup")

    def failure(args, **kwargs):
        if args[-2:] == ["db", "app"]:
            raise RuntimeError("recovery startup failed")
        return docker(args, **kwargs)

    with pytest.raises(RuntimeError, match="recovery-failed"):
        module.deploy(installed, "candidate image", "candidate", failure, {})
    assert json.loads((installed / "release.json").read_text())["status"] == "blocked"
