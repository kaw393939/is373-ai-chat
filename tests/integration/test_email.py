import asyncio
import json
import os

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from sqlalchemy import select

from app.email import drain, enqueue
from app.models import EmailOutbox, Recovery, User, now
from app.security import digest
from app.services import consume_link
from tests.conftest import PASSWORD, login


def enable(application):
    config = application.state.config
    config.email_provider = "mock"
    config.email_encryption_key = Fernet.generate_key().decode()
    return config


async def last_link(application, kind):
    config = application.state.config
    async with application.state.factory() as db:
        items = (
            await db.scalars(select(EmailOutbox).order_by(EmailOutbox.created_at.desc()))
        ).all()
        payload = json.loads(Fernet(config.email_encryption_key.encode()).decrypt(items[0].payload))
        assert payload["to"] == ["learner@example.org"]
        token = payload["text"].split(f"#{kind}=")[1].split()[0]
        assert token not in items[0].payload
        stored = await db.get(Recovery, digest(token))
        assert stored and stored.purpose == kind
        return token


async def test_registration_verification_approval_and_email_recovery(client, application):
    config = enable(application)
    config.registration_policy = "approval"
    body = {"email": "learner@example.org", "password": PASSWORD}
    response = await client.post("/api/auth/register", json=body)
    assert response.status_code == 201 and "inbox" in response.json()["message"]
    assert (await client.post("/api/auth/register", json=body)).json() == response.json()
    assert (await client.post("/api/auth/login", json=body)).status_code == 401
    assert (await client.get("/api/auth/options")).json()["email_enabled"]
    token = await last_link(application, "verify")
    assert (
        await client.post("/api/auth/reset", json={"token": token, "password": PASSWORD})
    ).status_code == 400
    assert (await client.post("/api/auth/verify", json={"token": "bad"})).status_code == 400
    assert (await client.post("/api/auth/verify", json={"token": token})).status_code == 200
    assert (await client.post("/api/auth/verify", json={"token": token})).status_code == 400
    assert (await client.post("/api/auth/login", json=body)).status_code == 401
    await login(client)
    users = (await client.get("/api/admin/users")).json()
    learner = next(u for u in users if u["email"] == body["email"])
    assert learner["email_verified"]
    assert (
        await client.patch(
            f"/api/admin/users/{learner['id']}",
            json={"role": "user", "active": True, "approved": True},
        )
    ).status_code == 200
    await login(client, body["email"])
    known = await client.post("/api/auth/email", json={"email": body["email"]})
    unknown = await client.post("/api/auth/email", json={"email": "missing@example.org"})
    assert known.json() == unknown.json() and known.status_code == 200
    reset = await last_link(application, "reset")
    assert (await client.post("/api/auth/verify", json={"token": reset})).status_code == 400
    assert (
        await client.post(
            "/api/auth/reset", json={"token": reset, "password": "new-learner-password-123"}
        )
    ).status_code == 204
    assert (await client.get("/api/auth/me")).status_code == 401
    await login(client, body["email"], "new-learner-password-123")
    await drain(application.state.factory, config, application.state.mailer)
    assert len(application.state.mailer.messages) == 3
    async with application.state.factory() as db:
        items = (await db.scalars(select(EmailOutbox))).all()
        assert all(i.status == "sent" and i.payload == "" and i.provider_id for i in items)


async def test_resend_eligibility_expiration_and_limits(client, application):
    assert (
        await client.post("/api/auth/email", json={"email": "learner@example.org"})
    ).status_code == 503
    config = enable(application)
    assert (
        await client.post("/api/auth/email?purpose=bad", json={"email": "learner@example.org"})
    ).status_code == 400
    await client.post(
        "/api/auth/register", json={"email": "learner@example.org", "password": PASSWORD}
    )
    assert (
        await client.post("/api/auth/email?purpose=verify", json={"email": "learner@example.org"})
    ).status_code == 200
    assert (
        await client.post("/api/auth/email?purpose=verify", json={"email": "learner@example.org"})
    ).status_code == 429
    token = await last_link(application, "verify")
    async with application.state.factory() as db:
        tokens = (await db.scalars(select(Recovery))).all()
        for item in tokens:
            item.expires_at = now() - 1
        outbox = (await db.scalars(select(EmailOutbox))).all()
        for item in outbox:
            item.expires_at = now() - 1
        await db.commit()
    assert (await client.post("/api/auth/verify", json={"token": token})).status_code == 400
    await drain(application.state.factory, config, application.state.mailer)
    async with application.state.factory() as db:
        assert all(
            i.status == "expired" and not i.payload
            for i in (await db.scalars(select(EmailOutbox))).all()
        )
        for _ in range(80):
            db.add(EmailOutbox(payload="encrypted", expires_at=now() + 100))
        await db.commit()
    assert (
        await client.post(
            "/api/auth/register", json={"email": "over-quota@example.org", "password": PASSWORD}
        )
    ).status_code == 503
    async with application.state.factory() as db:
        assert not await db.scalar(select(User).where(User.email == "over-quota@example.org"))


async def test_retry_is_bounded_and_erases_payload(application, monkeypatch):
    config = enable(application)
    async with application.state.factory() as db:
        await enqueue(db, config, "learner@example.org", "Test", "A private message")
        await db.commit()

    class Unavailable:
        keys = []

        async def send(self, payload, key):
            self.keys.append(key)
            raise RuntimeError("provider unavailable")

    failed = Unavailable()
    for _ in range(6):
        await drain(application.state.factory, config, failed)
        async with application.state.factory() as db:
            item = await db.scalar(select(EmailOutbox))
            assert item.next_attempt > now()
            item.next_attempt = now() - 1
            await db.commit()
    assert len(set(failed.keys)) == 1 and len(failed.keys) == 6
    async with application.state.factory() as db:
        item = await db.scalar(select(EmailOutbox))
        assert item.status == "failed" and item.payload == ""
    await drain(application.state.factory, config, failed)


async def test_batch_bound_and_rolling_month_quota(application):
    async with application.state.factory() as db:
        await enqueue(db, application.state.config, "learner@example.org", "Test", "Test")
        assert not await db.scalar(select(EmailOutbox))
    config = enable(application)
    async with application.state.factory() as db:
        for _ in range(11):
            await enqueue(db, config, "learner@example.org", "Test", "Test")
        await db.commit()
    await drain(application.state.factory, config, application.state.mailer)
    assert len(application.state.mailer.messages) == 10
    async with application.state.factory() as db:
        # More than a day ago: daily quota available, rolling monthly quota exhausted.
        for _ in range(2000):
            db.add(
                EmailOutbox(
                    payload="", status="sent", created_at=now() - 86400 * 2, expires_at=now() - 1
                )
            )
        await db.commit()
        import pytest
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            await enqueue(db, config, "learner@example.org", "Test", "Test")


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="Real PostgreSQL locking",
)
async def test_sibling_links_only_one_redemption(application):
    async with application.state.factory() as db:
        owner = await db.scalar(select(User))
        for value in ["first-link", "second-link"]:
            db.add(
                Recovery(
                    digest=digest(value), user_id=owner.id, purpose="reset", expires_at=now() + 300
                )
            )
        await db.commit()

    async def redeem(value):
        async with application.state.factory() as db:
            try:
                await consume_link(db, value, "reset")
                await asyncio.sleep(0.05)
                await db.commit()
                return 204
            except HTTPException as exc:
                return exc.status_code

    assert sorted(await asyncio.gather(redeem("first-link"), redeem("second-link"))) == [204, 400]
