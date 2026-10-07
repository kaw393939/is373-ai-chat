"""Create a disposable local browser target, run journeys, then remove it.

This is a teaching/test harness, never a production entry point. It binds only
loopback, rejects an occupied port, and ignores existing application credentials.
"""

import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from tests.targets import verify_browser_target  # noqa: E402


def main():
    with socket.socket() as port:
        port.bind(("127.0.0.1", 9001))  # Refuse a server we did not start.
    with tempfile.TemporaryDirectory(prefix="chat-browser-lab-") as directory:
        env = dict(os.environ)
        for name in Settings.model_fields:
            env.pop(name.upper(), None)
        config = Settings.model_construct()
        env.update({name.upper(): str(value) for name, value in config.model_dump().items()})
        env.update(
            DATABASE_URL=f"sqlite+aiosqlite:///{directory}/browser.db",
            ADMIN_PASSWORD="browser-workshop-admin-1234",
            E2E_URL="http://127.0.0.1:9001",
            E2E_TARGET_TOKEN=secrets.token_hex(32),
            E2E_TEMP_ROOT=directory,
            E2E_STATIC_DIR=str(ROOT / "frontend/dist"),
            E2E_ADMIN_EMAIL="admin@example.org",
            E2E_ADMIN_PASSWORD="browser-workshop-admin-1234",
        )
        for args in [["-m", "alembic", "upgrade", "head"], ["-m", "app.cli", "admin"]]:
            subprocess.run([sys.executable, *args], cwd=ROOT, env=env, check=True)
        with open(Path(directory) / "server.log", "w+") as log:
            server = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "tests.browser_app:create_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "9001",
                ],
                cwd=ROOT,
                env=env,
                stdout=log,
                stderr=log,
            )
            try:
                for attempt in range(60):
                    if server.poll() is not None:
                        raise RuntimeError("Disposable server exited before readiness")
                    try:
                        verify_browser_target(env["E2E_URL"], env["E2E_TARGET_TOKEN"])
                        break
                    except Exception:
                        if attempt == 59:
                            raise
                        time.sleep(0.25)
                subprocess.run(
                    [sys.executable, "-m", "pytest", "tests/e2e", "-v"],
                    cwd=ROOT,
                    env=env,
                    check=True,
                )
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()
                if server.returncode not in {0, -15}:
                    log.seek(0)
                    print(log.read(), file=sys.stderr)


if __name__ == "__main__":
    main()
