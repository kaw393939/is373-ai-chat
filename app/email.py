"""Encrypted transactional outbox: database transaction first, HTTPS delivery later."""

import json
from typing import Protocol

import httpx
from cryptography.fernet import Fernet
from fastapi import HTTPException
from sqlalchemy import func, select, text

from app.models import EmailOutbox, Recovery, now
from app.security import digest, secret_token


class MailCapacityExceeded(HTTPException):
    """Internal admission refusal; public routes conceal account eligibility."""

    def __init__(self):
        super().__init__(503, "Email delivery capacity reached; try again later")


class Mailer(Protocol):
    async def send(self, payload: dict, key: str) -> str: ...


class MockMailer:
    def __init__(self):
        self.messages = []

    async def send(self, payload, key):
        self.messages.append(payload)
        return key


class ResendMailer:
    def __init__(self, config):
        self.key = config.resend_api_key

    async def send(self, payload, key):
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": "Bearer " + self.key, "Idempotency-Key": key},
                json=payload,
            )
            response.raise_for_status()
            return response.json()["id"]


def make_mailer(config):
    return ResendMailer(config) if config.email_provider == "resend" else MockMailer()


async def enqueue(db, config, recipient, subject, message, ttl=1800):
    if config.email_provider == "disabled":
        return
    # Dedicated transaction lock avoids mixing mail and chat/user lock order.
    if db.bind.dialect.name == "postgresql":
        await db.execute(text("SELECT pg_advisory_xact_lock(37302)"))
    else:
        await db.execute(text("UPDATE role_budgets SET role=role WHERE role='user'"))
    instant = now()
    for start, limit in ((instant - instant % 86400, 80), (instant - 30 * 86400, 2000)):
        count = await db.scalar(
            select(func.count()).select_from(EmailOutbox).where(EmailOutbox.created_at >= start)
        )
        if count >= limit:
            raise MailCapacityExceeded()
    payload = {
        "from": config.email_from,
        "to": [recipient],
        "reply_to": config.email_reply_to,
        "subject": subject,
        "text": message,
    }
    encrypted = Fernet(config.email_encryption_key.encode()).encrypt(json.dumps(payload).encode())
    db.add(EmailOutbox(payload=encrypted.decode(), expires_at=instant + ttl))


async def token_email(db, config, user, purpose):
    value = secret_token()
    # Previously sent links remain valid until used/expired; anonymous resend cannot
    # invalidate an owner's existing link. Reset/verification invalidate siblings.
    db.add(
        Recovery(digest=digest(value), user_id=user.id, purpose=purpose, expires_at=now() + 1800)
    )
    label = "Verify your email" if purpose == "verify" else "Reset your password"
    approval = (
        (
            "Registration also requires administrator approval."
            if config.registration_policy == "approval" and not user.approved
            else "After verification, you can sign in."
        )
        if purpose == "verify"
        else "Use your new password to sign in after resetting it."
    )
    await enqueue(
        db,
        config,
        user.email,
        label + " · Firehose360",
        f"{label}: {config.base_url}/#{purpose}={value}\n\n"
        "This link expires in 30 minutes and works once. Ignore it if you did not request it.\n"
        + approval,
    )


async def drain(factory, config, mailer):
    """Small bounded batches. Row locks plus provider idempotency prevent duplicates."""
    for _ in range(10):
        async with factory() as db:
            item = await db.scalar(
                select(EmailOutbox)
                .where(EmailOutbox.status == "pending", EmailOutbox.next_attempt <= now())
                .order_by(EmailOutbox.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if not item:
                return
            if item.expires_at <= now():
                item.status, item.payload = "expired", ""
            else:
                item.attempts += 1
                try:
                    payload = json.loads(
                        Fernet(config.email_encryption_key.encode()).decrypt(item.payload)
                    )
                    item.provider_id = await mailer.send(payload, "chat-email/" + item.id)
                    item.status, item.payload = "sent", ""
                except Exception:
                    # Never log provider responses, recipients, credentials or links.
                    item.next_attempt = now() + min(300, 2**item.attempts * 10)
                    if item.attempts >= 6:
                        item.status, item.payload = "failed", ""
            await db.commit()
