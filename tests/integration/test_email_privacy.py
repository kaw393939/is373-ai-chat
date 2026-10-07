"""Public receipts conceal eligibility; account/link/outbox remain transactional."""

import json

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EmailOutbox, Recovery, User, now
from tests.conftest import PASSWORD, login
from tests.integration.test_email import enable, last_link


@pytest.mark.parametrize(
    "policy,approval_first", [("open", False), ("approval", False), ("approval", True)]
)
async def test_approval_and_verification_have_accurate_next_steps(
    client, application, policy, approval_first
):
    config = enable(application)
    config.registration_policy = policy
    body = {"email": "learner@example.org", "password": PASSWORD}
    receipt = await client.post("/api/auth/register", json=body)
    duplicate = await client.post("/api/auth/register", json=body)
    assert (
        receipt.status_code == duplicate.status_code == 201 and receipt.json() == duplicate.json()
    )
    async with application.state.factory() as db:
        user = await db.scalar(select(User).where(User.email == body["email"]))
        uid = user.id
        item = await db.scalar(select(EmailOutbox))
        text = json.loads(Fernet(config.email_encryption_key.encode()).decrypt(item.payload))[
            "text"
        ]
        assert ("requires administrator approval" in text) == (policy == "approval")
    token = await last_link(application, "verify")
    if approval_first:
        await login(client)
        response = await client.patch(
            f"/api/admin/users/{uid}", json={"role": "user", "active": True, "approved": True}
        )
        assert response.status_code == 200
        async with application.state.factory() as db:
            rows = (await db.scalars(select(EmailOutbox).order_by(EmailOutbox.created_at))).all()
            approval = json.loads(
                Fernet(config.email_encryption_key.encode()).decrypt(rows[-1].payload)
            )["text"]
            assert "Verify your email" in approval and "now sign in" not in approval
    result = await client.post("/api/auth/verify", json={"token": token})
    assert result.status_code == 200
    assert ("You can sign in" in result.json()["message"]) == (policy == "open" or approval_first)
    if policy == "approval" and not approval_first:
        await login(client)
        await client.patch(
            f"/api/admin/users/{uid}", json={"role": "user", "active": True, "approved": True}
        )
        async with application.state.factory() as db:
            item = await db.scalar(select(EmailOutbox).order_by(EmailOutbox.created_at.desc()))
            assert (
                "now sign in"
                in json.loads(Fernet(config.email_encryption_key.encode()).decrypt(item.payload))[
                    "text"
                ]
            )
    await login(client, body["email"])


async def test_delivery_exhaustion_does_not_disclose_accounts_or_leave_links(client, application):
    enable(application)
    async with application.state.factory() as db:
        for _ in range(80):
            db.add(EmailOutbox(payload="synthetic", expires_at=now() + 300))
        await db.commit()
    known = await client.post("/api/auth/email", json={"email": "admin@example.org"})
    unknown = await client.post("/api/auth/email", json={"email": "missing@example.org"})
    assert known.status_code == unknown.status_code == 200 and known.json() == unknown.json()
    existing = await client.post(
        "/api/auth/register", json={"email": "admin@example.org", "password": PASSWORD}
    )
    new = await client.post(
        "/api/auth/register", json={"email": "new@example.org", "password": PASSWORD}
    )
    assert existing.status_code == new.status_code == 201 and existing.json() == new.json()
    async with application.state.factory() as db:
        assert not await db.scalar(select(User).where(User.email == "new@example.org"))
        assert await db.scalar(select(func.count()).select_from(Recovery)) == 0
        assert await db.scalar(select(func.count()).select_from(EmailOutbox)) == 80


async def test_registration_unique_race_has_same_public_receipt(client, application, monkeypatch):
    enable(application)
    original = AsyncSession.flush

    async def lost_unique_race(db, *args, **kwargs):
        if any(isinstance(row, User) and row.email == "race@example.org" for row in db.new):
            raise IntegrityError("synthetic competing insert", {}, ValueError("unique"))
        return await original(db, *args, **kwargs)

    monkeypatch.setattr(AsyncSession, "flush", lost_unique_race)
    raced = await client.post(
        "/api/auth/register", json={"email": "race@example.org", "password": PASSWORD}
    )
    existing = await client.post(
        "/api/auth/register", json={"email": "admin@example.org", "password": PASSWORD}
    )
    assert raced.status_code == existing.status_code == 201 and raced.json() == existing.json()
    async with application.state.factory() as db:
        assert not await db.scalar(select(User).where(User.email == "race@example.org"))
        assert not await db.scalar(select(Recovery))
