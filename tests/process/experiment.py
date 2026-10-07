"""Run bounded process faults against two replicas and disposable PostgreSQL.

Use --image in Linux CI for the exact tested artifact. --local is a source-only
debugging path. Production targets/containers are neither accepted nor discovered.
"""

import argparse
import asyncio
import json
import os
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import httpx  # noqa: E402
from cryptography.fernet import Fernet  # noqa: E402
from sqlalchemy import delete, func, select, text  # noqa: E402

from app.config import Settings  # noqa: E402
from app.db import database  # noqa: E402
from app.email import enqueue  # noqa: E402
from app.models import Base, EmailOutbox, Generation, Message, RoleBudget, User  # noqa: E402
from app.security import hash_password  # noqa: E402
from tests.process.safety import URLS, process_database, process_url, verify_identity  # noqa: E402

PASSWORD = "synthetic-process-workshop-password"


def command(args, **kwargs):
    result = subprocess.run(args, capture_output=True, timeout=180, **kwargs)
    if result.returncode:
        raise RuntimeError("Process fixture command failed: " + args[0])
    return result.stdout


class Replica:
    def __init__(self, experiment, number, directory):
        self.experiment, self.number = experiment, number
        self.name = "chat-process-" + experiment.token[:12] + "-" + str(number)
        self.log = open(Path(directory) / (str(number) + ".log"), "wb")
        self.server, self.created = None, False

    async def start(self, mail="disabled"):
        fixture = {
            "PROCESS_DATABASE_URL": self.experiment.url,
            "PROCESS_ALLOW_RESET": "process_test",
            "PROCESS_NONCE": self.experiment.token,
            "PROCESS_REPLICA": str(self.number),
            "PROCESS_MAIL_MODE": mail,
            "PROCESS_MAIL_KEY": self.experiment.mail_key,
            "PROCESS_COMMIT": self.experiment.commit,
            "PROCESS_STATIC_DIR": "/app/frontend/dist"
            if self.experiment.image
            else str(ROOT / "frontend/dist"),
        }
        arguments = [
            "uvicorn",
            "tests.process_app:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(9002 + self.number),
            "--timeout-graceful-shutdown",
            "10",
            "--no-access-log",
        ]
        if self.experiment.image:
            if self.created:
                await asyncio.to_thread(command, ["docker", "rm", "-f", self.name])
            docker = [
                "docker",
                "run",
                "-d",
                "--name",
                self.name,
                "--network",
                "host",
                "--read-only",
                "--no-healthcheck",  # Factory ports have explicit nonce/readiness probes.
                "--user",
                "10001:10001",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--pids-limit",
                "128",
                "--memory",
                "512m",
                "--tmpfs",
                "/tmp:size=64m",
                "-v",
                str(ROOT / "tests") + ":/app/tests:ro",
            ]
            for key, value in fixture.items():
                docker += ["-e", key + "=" + value]
            await asyncio.to_thread(command, [*docker, self.experiment.image, *arguments])
            self.created = True
        else:
            environment = dict(os.environ)
            for field in Settings.model_fields:
                environment.pop(field.upper(), None)
            self.server = subprocess.Popen(
                [sys.executable, "-m", *arguments],
                cwd=ROOT,
                env={**environment, **fixture},
                stdout=self.log,
                stderr=self.log,
            )
        for attempt in range(80):
            try:
                async with httpx.AsyncClient(trust_env=False, timeout=2) as client:
                    response = await client.get(
                        process_url(URLS[self.number]) + "/_process/identity"
                    )
                    response.raise_for_status()
                    verify_identity(response.json(), self.experiment.token, self.number)
                    health = (await client.get(URLS[self.number] + "/api/health")).json()
                    assert (
                        health["commit"] == self.experiment.commit
                        and health["version"] == self.experiment.version
                    )
                return
            except (httpx.HTTPError, AssertionError):
                if attempt == 79:
                    raise RuntimeError("Process replica did not become ready") from None
                await asyncio.sleep(0.25)

    async def terminate(self, hard=False):
        started = time.monotonic()
        if self.experiment.image:
            if not self.created:
                return 0
            state = json.loads(
                await asyncio.to_thread(
                    command, ["docker", "inspect", self.name, "--format", "{{json .State}}"]
                )
            )
            if not state["Running"]:
                return 0
            await asyncio.to_thread(
                command, ["docker", "kill", "--signal", "KILL" if hard else "TERM", self.name]
            )
            for _ in range(80):
                state = json.loads(
                    await asyncio.to_thread(
                        command, ["docker", "inspect", self.name, "--format", "{{json .State}}"]
                    )
                )
                if not state["Running"]:
                    if not hard:
                        assert state["ExitCode"] in {0, 143}, (
                            "Graceful worker required forced killing"
                        )
                    return time.monotonic() - started
                await asyncio.sleep(0.25)
            raise AssertionError("Worker shutdown exceeded 20 seconds")
        if self.server and self.server.poll() is None:
            self.server.send_signal(signal.SIGKILL if hard else signal.SIGTERM)
            await asyncio.to_thread(self.server.wait, timeout=20)
            if not hard:
                assert self.server.returncode in {0, -15}
        return time.monotonic() - started

    async def close(self):
        try:
            await self.terminate(hard=True)
            if self.experiment.image and self.created:
                await asyncio.to_thread(command, ["docker", "rm", "-f", self.name])
        finally:
            self.log.close()


class Experiment:
    def __init__(self, image, case="all"):
        self.url = process_database(
            os.environ["PROCESS_DATABASE_URL"], os.environ.get("PROCESS_ALLOW_RESET")
        )
        self.token, self.mail_key = secrets.token_hex(32), Fernet.generate_key().decode()
        self.image, self.commit = image, "local-working-tree"
        self.version = (ROOT / "VERSION").read_text().strip()
        self.case = case
        if image:
            labels = json.loads(
                command(
                    ["docker", "image", "inspect", image, "--format", "{{json .Config.Labels}}"]
                )
            )
            self.commit = os.environ["GITHUB_SHA"]
            assert labels["org.opencontainers.image.revision"] == self.commit
            assert labels["org.opencontainers.image.version"] == self.version
            # Freeze the local content ID so a retag cannot change later replicas.
            self.image = (
                command(["docker", "image", "inspect", image, "--format", "{{.Id}}"])
                .decode()
                .strip()
            )
        self.engine, self.factory = database(self.url)
        self.evidence = {
            "status": "running",
            "mode": "exact-image" if image else "local-source-debug",
            "commit": self.commit,
            "version": self.version,
            "image": self.image,
            "checks": [],
            "scope": case,
        }
        self.held, self.clients, self.replicas, self.users, self.tokens = [], [], [], [], []

    async def initialize(self):
        # No migration/reset is permitted until the database and ports are guarded.
        for url in URLS:
            with socket.socket() as port:
                port.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                port.bind(("127.0.0.1", int(url.rsplit(":", 1)[1])))
        defaults = {
            key.upper(): str(value)
            for key, value in Settings.model_construct().model_dump().items()
        }
        defaults.update(
            DATABASE_URL=self.url, APP_ENV="development", EMAIL_PROVIDER="disabled", PROVIDER="mock"
        )
        if self.image:
            args = ["docker", "run", "--rm", "--network", "host"]
            for key, value in defaults.items():
                args += ["-e", key + "=" + value]
            await asyncio.to_thread(command, [*args, self.image, "alembic", "upgrade", "head"])
        else:
            await asyncio.to_thread(
                command,
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=ROOT,
                env={**os.environ, **defaults},
            )
        async with self.factory() as db:
            for table in reversed(Base.metadata.sorted_tables):
                await db.execute(delete(table))
            await db.execute(text("CREATE SCHEMA IF NOT EXISTS process_fixture"))
            await db.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS process_fixture.receipts (key varchar(128) PRIMARY KEY, attempts integer NOT NULL, accepted integer NOT NULL CHECK (accepted = 1))"
                )
            )
            await db.execute(text("DELETE FROM process_fixture.receipts"))
            db.add_all(
                [
                    RoleBudget(role="user", max_concurrent=4, daily_units=1000000),
                    RoleBudget(role="admin"),
                ]
            )
            hashed = hash_password(PASSWORD)
            for index in range(3):
                user = User(
                    email=f"process-{index}@example.org",
                    password_hash=hashed,
                    approved=True,
                    email_verified=True,
                    max_concurrent=4,
                )
                db.add(user)
                self.users.append(user)
            await db.commit()

    async def connect(self):
        self.clients = [
            httpx.AsyncClient(
                base_url=process_url(url),
                trust_env=False,
                follow_redirects=False,
                timeout=20,
                headers={"Origin": URLS[0]},
            )
            for url in URLS
        ]
        for user in self.users:
            response = await self.clients[0].post(
                "/api/auth/login", json={"email": user.email, "password": PASSWORD}
            )
            assert response.status_code == 200, "Fixture login failed"
            self.tokens.append({"Authorization": "Bearer " + response.json()["access_token"]})

    async def conversation(self, owner=0):
        response = await self.clients[0].post("/api/conversations", headers=self.tokens[owner])
        assert response.status_code == 201
        return response.json()["id"]

    async def hold(self, replica, owner, cid, key=None):
        client = self.clients[replica]
        request = client.build_request(
            "POST",
            f"/api/conversations/{cid}/stream",
            headers=self.tokens[owner],
            json={"content": "hold", "request_key": key or uuid4().hex, "model": "default"},
        )
        response = await client.send(request, stream=True)
        result = {"status": response.status_code}
        if response.status_code != 200:
            await response.aread()
            await response.aclose()
            return result
        iterator, kind, rid = response.aiter_lines(), None, None
        self.held.append((response, iterator))
        async for line in iterator:
            if line.startswith("event: "):
                kind = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
                if kind == "started":
                    rid = data["run_id"]
                if kind == "delta":
                    assert rid and data["text"].startswith("synthetic partial")
                    return {**result, "run_id": rid}
        raise AssertionError("Held provider produced no partial stream")

    async def active(self):
        async with self.factory() as db:
            return await db.scalar(
                select(func.count()).select_from(Generation).where(Generation.status == "streaming")
            )

    async def release(self):
        for response, iterator in self.held:
            await response.aclose()
            await iterator.aclose()
        self.held.clear()
        for _ in range(100):
            if await self.active() == 0:
                return
            await asyncio.sleep(0.1)
        raise AssertionError("Disconnected streams retained capacity")

    async def admission(self):
        chats = [await self.conversation(index) for index in range(3)]
        outcomes = await asyncio.gather(
            self.hold(0, 0, chats[0]), self.hold(1, 1, chats[1]), self.hold(1, 2, chats[2])
        )
        assert sorted(value["status"] for value in outcomes) == [200, 200, 429]
        assert await self.active() == 2
        await self.release()
        self.evidence["checks"].append(
            {"case": "global race across two replicas", "accepted": 2, "refused": 1}
        )

        async with self.factory() as db:
            user = await db.get(User, self.users[0].id)
            user.max_concurrent = 1
            await db.commit()
        second = await self.conversation()
        outcomes = await asyncio.gather(self.hold(0, 0, chats[0]), self.hold(1, 0, second))
        assert sorted(value["status"] for value in outcomes) == [200, 429]
        assert await self.active() == 1
        await self.release()
        self.evidence["checks"].append(
            {"case": "user race across two replicas", "accepted": 1, "refused": 1}
        )

        async with self.factory() as db:
            user = await db.get(User, self.users[0].id)
            user.max_concurrent = 4
            await db.commit()
        outcomes = await asyncio.gather(self.hold(0, 0, chats[0]), self.hold(1, 0, chats[0]))
        assert sorted(value["status"] for value in outcomes) == [200, 429]
        await self.release()
        key = uuid4().hex
        outcomes = await asyncio.gather(
            self.hold(0, 0, chats[0], key), self.hold(1, 0, chats[0], key)
        )
        assert sorted(value["status"] for value in outcomes) == [200, 409]
        await self.release()
        self.evidence["checks"].append(
            {
                "case": "conversation/replay races",
                "conversation_refusal": 429,
                "replay_refusal": 409,
            }
        )

    async def graceful(self):
        cid = await self.conversation()
        held = await self.hold(0, 0, cid)
        assert held["status"] == 200
        elapsed = await self.replicas[0].terminate()
        assert elapsed < 15, "10-second graceful deadline lacked cleanup margin"
        async with self.factory() as db:
            run = await db.get(Generation, held["run_id"])
            partial = await db.get(Message, run.message_id)
            assert run.status == "cancelled" and partial.content.startswith("synthetic partial")
        await self.release()
        self.evidence["checks"].append(
            {
                "case": "SIGTERM active stream",
                "seconds": round(elapsed, 3),
                "terminal": run.status,
                "partial_characters": len(partial.content),
                "active_after": 0,
            }
        )
        await self.replicas[0].start()

    async def abrupt(self):
        cid, other = await self.conversation(), await self.conversation()
        held = await self.hold(0, 0, cid)
        assert held["status"] == 200
        async with self.factory() as db:
            run = await db.get(Generation, held["run_id"])
            lease = run.expires_at - run.created_at
            expires = run.expires_at
            assert 149 <= lease <= 151
            user = await db.get(User, self.users[0].id)
            user.max_concurrent = 1
            await db.commit()
        await self.replicas[0].terminate(hard=True)
        response = await self.clients[1].post(
            f"/api/conversations/{other}/stream",
            headers=self.tokens[0],
            json={"content": "quick", "request_key": uuid4().hex},
        )
        assert response.status_code == 429, "Killed worker reservation vanished before its lease"
        # Real wall-clock lease: no injected clock or modified expiry disguises recovery.
        await asyncio.sleep(max(0, expires - time.time()) + 0.5)
        response = await self.clients[1].post(
            f"/api/conversations/{other}/stream",
            headers=self.tokens[0],
            json={"content": "quick", "request_key": uuid4().hex},
        )
        assert response.status_code == 200 and '"complete"' in response.text
        async with self.factory() as db:
            old = await db.get(Generation, held["run_id"])
            partial = await db.get(Message, old.message_id)
            assert old.status == "interrupted"
            assert await db.scalar(
                select(Message.id).where(
                    Message.conversation_id == cid,
                    Message.role == "user",
                    Message.content == "hold",
                )
            )
        await self.release()
        self.evidence["checks"].append(
            {
                "case": "KILL lease recovery",
                "lease_seconds": round(lease, 3),
                "reclaimed_after_expiry_seconds": round(time.time() - expires, 3),
                "terminal": old.status,
                "surviving_partial_characters": len(partial.content),
                "prompt_and_reservation_survived": True,
            }
        )

    async def mail(self):
        await self.replicas[1].terminate()
        await self.replicas[0].start(mail="receipt")
        config = Settings(
            _env_file=None,
            app_env="development",
            provider="mock",
            database_url=self.url,
            email_provider="mock",
            email_encryption_key=self.mail_key,
        )
        async with self.factory() as db:
            await enqueue(
                db, config, "process-mail@example.org", "Synthetic restart", "No real mail is sent"
            )
            await db.commit()
            item = await db.scalar(select(EmailOutbox))
            item_id = item.id
        for _ in range(100):
            async with self.factory() as db:
                receipts = (
                    await db.execute(
                        text("SELECT key, attempts, accepted FROM process_fixture.receipts")
                    )
                ).all()
                if receipts:
                    break
            await asyncio.sleep(0.1)
        assert len(receipts) == 1 and receipts[0].attempts == receipts[0].accepted == 1
        await self.replicas[0].terminate(hard=True)
        async with self.factory() as db:
            pending = await db.get(EmailOutbox, item_id)
            assert pending.status == "pending" and pending.payload
        await self.replicas[0].start(mail="receipt")
        for _ in range(100):
            async with self.factory() as db:
                item = await db.get(EmailOutbox, item_id)
                if item.status == "sent":
                    receipts = (
                        await db.execute(
                            text("SELECT key, attempts, accepted FROM process_fixture.receipts")
                        )
                    ).all()
                    break
            await asyncio.sleep(0.1)
        assert item.status == "sent" and not item.payload
        assert len(receipts) == 1 and receipts[0].accepted == 1 and receipts[0].attempts == 2
        assert receipts[0].key == item.provider_id == "chat-email/" + item_id
        self.evidence["checks"].append(
            {
                "case": "mail accepted-before-commit KILL/restart",
                "provider_attempts": 2,
                "accepted_deliveries": 1,
                "outbox": "sent",
                "payload_erased": True,
            }
        )

    async def run(self):
        with tempfile.TemporaryDirectory(prefix="chat-process-") as directory:
            self.replicas = [Replica(self, index, directory) for index in range(2)]
            try:
                self.evidence["phase"] = "initialize"
                await self.initialize()
                await asyncio.gather(*(replica.start() for replica in self.replicas))
                if self.image:
                    pids = [
                        int(
                            await asyncio.to_thread(
                                command,
                                ["docker", "inspect", replica.name, "--format", "{{.State.Pid}}"],
                            )
                        )
                        for replica in self.replicas
                    ]
                else:
                    pids = [replica.server.pid for replica in self.replicas]
                assert len(set(pids)) == 2 and all(pid > 0 for pid in pids)
                self.evidence["separate_os_processes"] = True
                await self.connect()
                phases = (
                    ("admission", "graceful", "abrupt", "mail")
                    if self.case == "all"
                    else (self.case,)
                )
                for phase in phases:
                    self.evidence["phase"] = phase
                    print("Process experiment: " + phase, flush=True)
                    await getattr(self, phase)()
                self.evidence["status"] = "passed"
            finally:
                if self.evidence["status"] != "passed":
                    scratch = ROOT / ".state"
                    scratch.mkdir(mode=0o700, exist_ok=True)
                    private = Path(tempfile.mkdtemp(prefix="process-debug-", dir=scratch))
                    for replica in self.replicas:
                        replica.log.flush()
                        if self.image and replica.created:
                            result = subprocess.run(
                                ["docker", "logs", "--tail", "200", replica.name],
                                capture_output=True,
                                timeout=10,
                            )
                            data = result.stdout + result.stderr
                        else:
                            data = Path(replica.log.name).read_bytes()
                        path = private / (str(replica.number) + ".log")
                        path.write_bytes(data)
                        path.chmod(0o600)
                    print(
                        "Private process diagnostics: " + str(private.relative_to(ROOT)), flush=True
                    )
                for response, iterator in self.held:
                    await response.aclose()
                    await iterator.aclose()
                for client in self.clients:
                    await client.aclose()
                await asyncio.gather(*(replica.close() for replica in self.replicas))
                await self.engine.dispose()
                if self.evidence["status"] != "passed":
                    self.evidence["status"] = "failed"
                output = ROOT / "artifacts/process.json"
                output.parent.mkdir(exist_ok=True)
                output.write_text(json.dumps(self.evidence, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--image")
    mode.add_argument("--local", action="store_true")
    parser.add_argument(
        "--case",
        choices=["all", "admission", "graceful", "abrupt", "mail"],
        default="all",
        help="Focused debugging only; CI acceptance uses all",
    )
    args = parser.parse_args()
    asyncio.run(Experiment(args.image, args.case).run())


if __name__ == "__main__":
    main()
