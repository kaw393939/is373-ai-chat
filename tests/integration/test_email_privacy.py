"""Public receipts conceal eligibility; account/link/outbox remain transactional."""

import asyncio
import json

import httpx
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


@pytest.mark.parametrize("existing_outbox", [0, 80])
async def test_real_postgresql_duplicate_registration_is_private_and_atomic(
    client, application, monkeypatch, existing_outbox
):
    if application.state.engine.dialect.name != "postgresql":
        pytest.skip("Requires real PostgreSQL unique-conflict and transaction semantics")
    enable(application)
    async with application.state.factory() as db:
        seeded = [
            EmailOutbox(payload="synthetic-existing", expires_at=now() + 300)
            for _ in range(existing_outbox)
        ]
        db.add_all(seeded)
        await db.commit()
        existing_ids = {item.id for item in seeded}

    email = "pg-race@example.org"
    body = {"email": email, "password": PASSWORD}
    barrier = asyncio.Barrier(2)
    original = AsyncSession.flush
    arrivals, real_conflicts = set(), []

    async def simultaneous_user_inserts(db, *args, **kwargs):
        inserting = any(isinstance(row, User) and row.email == email for row in db.new)
        if inserting and id(db) not in arrivals:
            # register_account has already observed absence and added its user.
            # Neither request can flush until both reach this actual insert.
            arrivals.add(id(db))
            await asyncio.wait_for(barrier.wait(), timeout=10)
        try:
            return await original(db, *args, **kwargs)
        except IntegrityError as error:
            if inserting:
                real_conflicts.append(error.orig.sqlstate)
            raise  # PostgreSQL supplies the conflict; the test never invents one.

    monkeypatch.setattr(AsyncSession, "flush", simultaneous_user_inserts)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:8000"},
    ) as peer:
        first, second = await asyncio.wait_for(
            asyncio.gather(
                client.post("/api/auth/register", json=body),
                peer.post("/api/auth/register", json=body),
            ),
            timeout=20,
        )
    known = await client.post(
        "/api/auth/register", json={"email": "admin@example.org", "password": PASSWORD}
    )
    assert len(arrivals) == 2
    assert first.status_code == second.status_code == known.status_code == 201
    assert first.json() == second.json() == known.json()
    # With capacity, one insert commits and the other gets real SQLSTATE 23505.
    # With no capacity, each insert can succeed after its peer rolls back; both
    # entire units roll back, so there is no committed uniqueness conflict.
    assert real_conflicts == (["23505"] if existing_outbox == 0 else [])
    async with application.state.factory() as db:
        users = (await db.scalars(select(User).where(User.email == email))).all()
        links = (await db.scalars(select(Recovery))).all()
        outbox = (await db.scalars(select(EmailOutbox))).all()
        if existing_outbox:
            assert users == links == []
            assert {item.id for item in outbox} == existing_ids
            assert all(item.payload == "synthetic-existing" for item in outbox)
        else:
            assert len(users) == len(links) == len(outbox) == 1
            assert links[0].user_id == users[0].id and links[0].purpose == "verify"
