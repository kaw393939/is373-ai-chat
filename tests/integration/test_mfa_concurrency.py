"""Recovery consumption requires real PostgreSQL row-lock behavior."""

import asyncio

import httpx
import pytest
from sqlalchemy import select

from app.models import MfaChallenge, MfaRecovery, User, now
from app.security import digest
from tests.integration.test_mfa import enrolled


async def test_two_challenges_cannot_reuse_one_recovery_code(client, application, monkeypatch):
    if application.state.engine.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL lock semantics")
    _, _, session = await enrolled(client, application, monkeypatch)
    values = ["synthetic-password-bound-challenge-one", "synthetic-password-bound-challenge-two"]
    async with application.state.factory() as db:
        user = await db.scalar(select(User).where(User.role == "admin"))
        for value in values:
            db.add(MfaChallenge(digest=digest(value), user_id=user.id, expires_at=now() + 300))
        await db.commit()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application), base_url="http://localhost:8000"
    ) as peer:
        responses = await asyncio.gather(
            client.post(
                "/api/auth/mfa/verify",
                json={"challenge": values[0], "code": session["recovery_codes"][0]},
            ),
            peer.post(
                "/api/auth/mfa/verify",
                json={"challenge": values[1], "code": session["recovery_codes"][0]},
            ),
        )
    assert sorted(response.status_code for response in responses) == [200, 401]
    async with application.state.factory() as db:
        recovery = await db.get(MfaRecovery, digest(session["recovery_codes"][0]))
        assert recovery.used
