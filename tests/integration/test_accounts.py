from pathlib import Path

from sqlalchemy import select

from app.models import Family, Recovery, User, now
from app.security import digest
from tests.conftest import PASSWORD, login, signup


async def test_registration_login_logout_and_headers(client):
    assert (await client.get("/api/auth/me")).status_code == 401
    assert (await client.get("/")).status_code == 200
    assert (await client.get("/api/health")).json()["schema"] == "0001"
    assert (await client.get("/api/missing")).status_code == 404
    r = await client.post(
        "/api/auth/login", json={"email": "missing@example.org", "password": PASSWORD}
    )
    assert r.status_code == 401
    user = await signup(client)
    assert user["role"] == "user"
    assert (await client.get("/api/auth/me")).json()["email"] == user["email"]
    r = await client.post("/api/auth/register", json={"email": user["email"], "password": PASSWORD})
    assert r.status_code == 409
    r = await client.post("/api/auth/logout")
    assert r.status_code == 204 and "httponly" in r.headers["set-cookie"].lower()
    assert (await client.get("/api/auth/me")).status_code == 401
    assert (await client.post("/api/auth/logout")).status_code == 204
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]


async def test_refresh_rotation_reuse_and_csrf(client):
    await login(client)
    old = client.cookies.get("refresh")
    assert (
        await client.post("/api/auth/refresh", headers={"Origin": "https://evil.example"})
    ).status_code == 403
    r = await client.post("/api/auth/refresh")
    assert r.status_code == 200
    client.headers["Authorization"] = "Bearer " + r.json()["access_token"]
    assert client.cookies.get("refresh") != old
    client.cookies.clear()
    client.cookies.set("refresh", old)
    assert (await client.post("/api/auth/refresh")).status_code == 401
    assert (await client.get("/api/auth/me")).status_code == 401
    client.cookies.clear()
    assert (await client.post("/api/auth/refresh")).status_code == 401


async def test_pending_and_disabled_accounts(client, application):
    application.state.config.registration_policy = "approval"
    r = await client.post(
        "/api/auth/register", json={"email": "pending@example.org", "password": PASSWORD}
    )
    assert "approve" in r.json()["message"]
    assert (
        await client.post(
            "/api/auth/login", json={"email": "pending@example.org", "password": PASSWORD}
        )
    ).status_code == 401
    async with application.state.factory() as db:
        user = await db.scalar(select(User).where(User.email == "pending@example.org"))
        user.approved = True
        user.active = False
        await db.commit()
    assert (
        await client.post("/api/auth/login", json={"email": user.email, "password": PASSWORD})
    ).status_code == 401
    assert (
        await client.post(
            "/api/auth/login", json={"email": "admin@example.org", "password": "wrong"}
        )
    ).status_code == 401
    assert (
        await client.post(
            "/api/auth/login",
            headers={"Origin": "https://evil.example"},
            json={"email": "admin@example.org", "password": PASSWORD},
        )
    ).status_code == 403


async def test_expired_family_and_invalid_jwt(client, application):
    await login(client)
    async with application.state.factory() as db:
        family = await db.scalar(select(Family))
        family.expires_at = now() - 1
        await db.commit()
    assert (await client.post("/api/auth/refresh")).status_code == 401
    assert (await client.get("/api/auth/me")).status_code == 401
    client.headers["Authorization"] = "Bearer bogus"
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_recovery_changes_password_revokes_sessions(client, application):
    admin = await login(client)
    r = await client.post(f"/api/admin/users/{admin['id']}/recovery")
    token = r.json()["url"].split("#reset=")[1]
    assert (
        await client.post(
            "/api/auth/reset", json={"token": token, "password": "changed-workshop-password"}
        )
    ).status_code == 204
    assert (await client.get("/api/auth/me")).status_code == 401
    assert (
        await client.post("/api/auth/reset", json={"token": token, "password": PASSWORD})
    ).status_code == 400
    await login(client, password="changed-workshop-password")
    assert (
        await client.post(
            "/api/auth/password", json={"email": admin["email"], "password": PASSWORD}
        )
    ).status_code == 204
    assert (await client.get("/api/auth/me")).status_code == 401
    assert (
        await client.post("/api/auth/reset", json={"token": "bad", "password": PASSWORD})
    ).status_code == 400


async def test_expired_recovery_and_auth_throttling(client, application, monkeypatch):
    user = await login(client)
    r = await client.post(f"/api/admin/users/{user['id']}/recovery")
    token = r.json()["url"].split("#reset=")[1]
    async with application.state.factory() as db:
        recovery = await db.get(Recovery, digest(token))
        recovery.expires_at = now() - 1
        await db.commit()
    assert (
        await client.post("/api/auth/reset", json={"token": token, "password": PASSWORD})
    ).status_code == 400
    instant = now()
    monkeypatch.setattr("app.services.now", lambda: instant)
    for _ in range(11):
        response = await client.post(
            "/api/auth/login", json={"email": "missing@example.org", "password": "bad"}
        )
    assert response.status_code == 429


async def test_static_missing_and_production_headers(client, application):
    Path(application.state.config.static_dir, "index.html").unlink()
    assert (await client.get("/")).status_code == 503
    application.state.config.app_env = "production"
    assert "max-age" in (await client.get("/api/health")).headers["strict-transport-security"]
    await login(client)
    assert (
        "secure" in client.cookies.jar._cookies["localhost.local"]["/api/auth"]["refresh"].__dict__
        or client.cookies.jar._cookies["localhost.local"]["/api/auth"]["refresh"].secure
    )
