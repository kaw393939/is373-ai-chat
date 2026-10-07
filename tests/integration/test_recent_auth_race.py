"""A password checked before a concurrent reset cannot authorize factor changes."""

import asyncio
import threading

import pytest

from app.models import Recovery, now
from app.security import digest, verify_password
from tests.conftest import PASSWORD, signup
from tests.integration.test_mfa import enrolled


@pytest.mark.parametrize(
    "operation,revocation",
    [
        ("replace", "reset"),
        ("password", "reset"),
        ("login", "reset"),
        ("replace", "logout"),
        ("password", "logout"),
    ],
)
async def test_concurrent_revocation_fences_recent_password_authority(
    client, application, monkeypatch, operation, revocation
):
    if operation == "login":
        user = await signup(client)
        session = {"user": user}
    else:
        _, _, session = await enrolled(client, application, monkeypatch)
    token = "synthetic-concurrent-reset-link"
    async with application.state.factory() as db:
        db.add(
            Recovery(
                digest=digest(token),
                user_id=session["user"]["id"],
                purpose="reset",
                expires_at=now() + 300,
            )
        )
        await db.commit()
    began, release = threading.Event(), threading.Event()

    def delayed_password_check(value, hashed):
        valid = verify_password(value, hashed)
        began.set()
        assert release.wait(5), "Synthetic password-check barrier timed out"
        return valid

    monkeypatch.setattr("app.main.verify_password", delayed_password_check)
    path, body = (
        ("/api/auth/login", {"email": session["user"]["email"], "password": PASSWORD})
        if operation == "login"
        else (
            "/api/auth/password",
            {"current_password": PASSWORD, "password": "stale-change-after-reset-123"},
        )
        if operation == "password"
        else (
            "/api/auth/mfa/replace",
            {"current_password": PASSWORD, "code": session["recovery_codes"][0]},
        )
    )
    pending = asyncio.create_task(client.post(path, json=body))
    try:
        assert await asyncio.to_thread(began.wait, 3)
        reset = (
            await client.post(
                "/api/auth/reset", json={"token": token, "password": "new-password-after-reset-123"}
            )
            if revocation == "reset"
            else await client.post("/api/auth/logout")
        )
        assert reset.status_code == 204
    finally:
        release.set()
    result = await pending
    assert result.status_code == 401
