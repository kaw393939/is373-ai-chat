"""Test-only ASGI factory mounted into the tested image, never shipped in it.

The held stream and durable synthetic mail receipts make termination windows
repeatable while exercising the real routes, admission, cleanup and outbox code.
No endpoint accepts a target, reset request, credential or integration choice.
"""

import asyncio
import os
from unittest.mock import patch

from sqlalchemy import text

from app.config import Settings
from app.db import database
from app.main import create_app as application
from app.providers import StreamEnd, TextDelta
from tests.process.safety import URLS, nonce, process_database


class HeldProvider:
    async def stream(self, messages, max_output):
        yield TextDelta("synthetic partial ")
        if messages[-1]["content"] == "hold":
            while True:
                await asyncio.sleep(0.25)
                yield TextDelta(".")
        yield StreamEnd("complete")


class ReceiptMailer:
    def __init__(self, url):
        self.engine, self.factory = database(url)

    async def send(self, payload, key):
        if any(not address.endswith("@example.org") for address in payload["to"]):
            raise ValueError("Synthetic mail fixture rejects real recipient addresses")
        async with self.factory() as db:
            attempts = await db.scalar(
                text(
                    "INSERT INTO process_fixture.receipts (key, attempts, accepted) VALUES (:key, 1, 1) ON CONFLICT (key) DO UPDATE SET attempts=receipts.attempts+1 RETURNING attempts"
                ),
                {"key": key},
            )
            await db.commit()  # Acceptance survives a killed application transaction.
        if attempts == 1:
            await asyncio.sleep(3600)  # Hold the accepted-before-outbox-commit window.
        return key  # Same idempotency key resumes the provider's accepted receipt.


def create_app():
    token = nonce(os.environ["PROCESS_NONCE"])
    url = process_database(os.environ["PROCESS_DATABASE_URL"], os.environ["PROCESS_ALLOW_RESET"])
    number = int(os.environ["PROCESS_REPLICA"])
    if number not in {0, 1} or os.environ["PROCESS_MAIL_MODE"] not in {"disabled", "receipt"}:
        raise ValueError("Invalid synthetic process fixture")
    for name in Settings.model_fields:
        os.environ.pop(name.upper(), None)
    mail = os.environ["PROCESS_MAIL_MODE"] == "receipt"
    config = Settings(
        _env_file=None,
        database_url=url,
        base_url=URLS[0],
        app_env="development",
        registration_policy="open",
        jwt_secret="synthetic-process-lab-only-with-no-production-authority",
        provider="mock",
        global_concurrency=2,
        email_provider="mock" if mail else "disabled",
        email_encryption_key=os.environ["PROCESS_MAIL_KEY"] if mail else "",
        admin_mfa_required=False,
        static_dir=os.environ["PROCESS_STATIC_DIR"],
        commit_sha=os.environ["PROCESS_COMMIT"],
    )
    if mail:
        with patch("app.main.make_mailer", return_value=ReceiptMailer(url)):
            app = application(config, HeldProvider())
    else:
        app = application(config, HeldProvider())

    @app.get("/_process/identity")
    async def identity():
        return {
            "nonce": token,
            "replica": number,
            "database": "process_test",
            "provider": "fault-mock",
            "mail": "synthetic-receipts" if mail else "disabled",
        }

    return app
