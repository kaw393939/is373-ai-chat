"""Real flock/pipeline behavior with CLI fakes and entirely temporary paths."""

import fcntl
import json
import os
import shutil
import subprocess
import tarfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(shutil.which("flock") is None, reason="Linux util-linux needed")


def fixture(tmp_path, fail_age=False):
    app, tools = tmp_path / "app", tmp_path / "tools"
    app.mkdir()
    tools.mkdir()
    for name, value in {
        ".env": "synthetic=only",
        "compose.yaml": "services: {}",
        "current-image": "old-image",
        "release.json": "{}",
    }.items():
        (app / name).write_text(value)
    recipient = tmp_path / "recipients"
    recipient.write_text("synthetic-public-recipient")
    state = tmp_path / "release"
    state.mkdir()
    source = (
        (ROOT / "deploy/backup.sh")
        .read_text()
        .replace("/opt/is373-ai-chat", str(app))
        .replace("/var/lib/chat-release", str(state))
        .replace("/run/lock/chat-backup.lock", str(tmp_path / "backup.lock"))
        .replace("/etc/chat-backup/recipients.txt", str(recipient))
        .replace("flock 8", f"touch '{tmp_path / 'before.lock'}'\nflock 8")
    )
    script = tmp_path / "backup.sh"
    script.write_text(source)
    docker = tools / "docker"
    docker.write_text(
        "#!/bin/sh\ncase \"$*\" in\n *pg_dump*) printf 'synthetic-dump';;\n *psql*) printf 'new-schema';;\n *prune*) :;;\n *) exit 1;;\nesac\n"
    )
    age = tools / "age"
    age.write_text("#!/bin/sh\n" + ("exit 1\n" if fail_age else 'cat > "$4"\n'))
    docker.chmod(0o700)
    age.chmod(0o700)
    environment = {**os.environ, "PATH": str(tools) + os.pathsep + os.environ["PATH"]}
    return app, state, script, environment


def test_backup_waits_for_release_lock_before_collecting_inventory(tmp_path):
    app, state, script, environment = fixture(tmp_path)
    with (state / "deploy.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        process = subprocess.Popen(
            ["bash", str(script)], env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        try:
            deadline = time.monotonic() + 5
            while not (tmp_path / "before.lock").exists():
                assert process.poll() is None, "Backup exited before requesting the shared lock"
                assert time.monotonic() < deadline
                time.sleep(0.01)
            assert process.poll() is None
            assert not (app / "backups").exists(), "Backup read the active release before the lock"
            (app / "current-image").write_text("new-image")
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, stderr.decode()
    archives = list((app / "backups").glob("daily-*.tar.age"))
    assert len(archives) == 1
    # The age fake only transports bytes, so inspect the real tar/manifest.
    with tarfile.open(archives[0]) as archive:
        manifest = json.load(archive.extractfile("./manifest.json"))
        assert manifest["image"] == "new-image" and manifest["schema"] == "new-schema"
        assert archive.extractfile("./database.dump").read() == b"synthetic-dump"
    assert not list((app / "backups").glob(".work-*"))


def test_failed_encryption_cannot_publish_a_ciphertext_or_leave_scratch(tmp_path):
    app, _, script, environment = fixture(tmp_path, fail_age=True)
    result = subprocess.run(["bash", str(script)], env=environment, capture_output=True, timeout=10)
    assert result.returncode != 0
    assert not list((app / "backups").iterdir())
