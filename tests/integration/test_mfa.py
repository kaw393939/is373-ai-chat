from cryptography.fernet import Fernet
from sqlalchemy import select

from app import mfa
from app.models import Family, MfaChallenge, MfaRecovery, User, now
from app.security import digest
from tests.conftest import PASSWORD, login, signup


async def challenge(client, email="admin@example.org"):
    response = await client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["mfa_required"] and "access_token" not in result and "user" not in result
    assert (
        "refresh=" not in response.headers.get("set-cookie", "")
        or "Max-Age=0" in response.headers["set-cookie"]
    )
    return result


def enable(application):
    config = application.state.config
    config.mfa_encryption_key = Fernet.generate_key().decode()
    config.admin_mfa_required = True
    return config


async def enrolled(client, application, monkeypatch):
    enable(application)
    monkeypatch.setattr(mfa, "now", lambda: 1_000_000)
    pending = await challenge(client)
    setup = (
        await client.post("/api/auth/mfa/enroll", json={"challenge": pending["challenge"]})
    ).json()
    result = await client.post(
        "/api/auth/mfa/verify",
        json={
            "challenge": pending["challenge"],
            "code": mfa.hotp(setup["secret"], 1_000_000 // 30),
        },
    )
    assert result.status_code == 200, result.text
    view = result.json()
    client.headers["Authorization"] = "Bearer " + view["access_token"]
    return pending, setup, view


async def test_required_admin_is_restricted_until_enrollment(client, application, monkeypatch):
    await login(client)
    old_cookie = client.cookies["refresh"]
    enable(application)
    assert (await client.get("/api/admin/users")).status_code == 401
    assert (await client.post("/api/auth/refresh")).status_code == 401
    pending, setup, view = await enrolled(client, application, monkeypatch)
    assert pending["enrollment_required"]
    assert (
        setup["otpauth_url"].startswith("otpauth://totp/")
        and setup["secret"] in setup["otpauth_url"]
    )
    assert len(view["recovery_codes"]) == len(set(view["recovery_codes"])) == 10
    assert (await client.get("/api/auth/mfa")).json() == {"enrolled": True}
    assert (await client.get("/api/admin/users")).status_code == 200
    assert (await client.post("/api/auth/refresh")).status_code == 200
    async with application.state.factory() as db:
        user = await db.scalar(select(User).where(User.role == "admin"))
        assert setup["secret"] not in user.mfa_secret
        assert (
            Fernet(application.state.config.mfa_encryption_key.encode())
            .decrypt(user.mfa_secret.encode())
            .decode()
            == setup["secret"]
        )
        codes = (await db.scalars(select(MfaRecovery))).all()
        assert {row.digest for row in codes} == {digest(code) for code in view["recovery_codes"]}
        assert all(row.digest not in view["recovery_codes"] for row in codes)
        sessions = (await db.scalars(select(Family))).all()
        assert any(row.revoked and not row.mfa_verified for row in sessions)
    client.cookies.set("refresh", old_cookie, path="/api/auth")
    assert (
        await client.post(
            "/api/auth/mfa/verify",
            json={"challenge": pending["challenge"], "code": view["recovery_codes"][0]},
        )
    ).status_code == 401


async def test_challenge_scope_expiry_attempts_and_repeated_setup(client, application, monkeypatch):
    config = enable(application)
    pending = await challenge(client)
    client.headers["Authorization"] = "Bearer " + pending["challenge"]
    assert (await client.get("/api/admin/users")).status_code == 401
    assert (
        await client.post("/api/auth/mfa/enroll", json={"challenge": "unknown"})
    ).status_code == 401
    first = await client.post("/api/auth/mfa/enroll", json={"challenge": pending["challenge"]})
    repeated = await client.post("/api/auth/mfa/enroll", json={"challenge": pending["challenge"]})
    assert first.json() == repeated.json()
    for _ in range(5):
        assert (
            await client.post(
                "/api/auth/mfa/verify", json={"challenge": pending["challenge"], "code": "bad"}
            )
        ).status_code == 401
    assert (
        await client.post(
            "/api/auth/mfa/verify",
            json={
                "challenge": pending["challenge"],
                "code": mfa.hotp(first.json()["secret"], int(now() // 30)),
            },
        )
    ).status_code == 401
    fresh = await challenge(client)
    async with application.state.factory() as db:
        row = await db.get(MfaChallenge, digest(fresh["challenge"]))
        row.expires_at = now() - 1
        await db.commit()
    assert (
        await client.post("/api/auth/mfa/enroll", json={"challenge": fresh["challenge"]})
    ).status_code == 401
    config.mfa_encryption_key = ""
    fresh = await challenge(client)
    assert (
        await client.post("/api/auth/mfa/enroll", json={"challenge": fresh["challenge"]})
    ).status_code == 503


async def test_factor_and_recovery_are_one_use_and_password_reset_not_bypass(
    client, application, monkeypatch
):
    _, setup, initial = await enrolled(client, application, monkeypatch)
    application.state.config.admin_mfa_required = False  # Enrollment itself still requires MFA.
    pending = await challenge(client)
    assert not pending["enrollment_required"]
    assert (
        await client.post("/api/auth/mfa/enroll", json={"challenge": pending["challenge"]})
    ).status_code == 400
    code = mfa.hotp(setup["secret"], 1_000_000 // 30)
    assert (
        await client.post(
            "/api/auth/mfa/verify", json={"challenge": pending["challenge"], "code": code}
        )
    ).status_code == 401
    result = await client.post(
        "/api/auth/mfa/verify",
        json={"challenge": pending["challenge"], "code": initial["recovery_codes"][0]},
    )
    assert result.status_code == 200 and "recovery_codes" not in result.json()
    client.headers["Authorization"] = "Bearer " + result.json()["access_token"]
    pending = await challenge(client)
    assert (
        await client.post(
            "/api/auth/mfa/verify",
            json={"challenge": pending["challenge"], "code": initial["recovery_codes"][0]},
        )
    ).status_code == 401
    monkeypatch.setattr(mfa, "now", lambda: 1_000_030)
    result = await client.post(
        "/api/auth/mfa/verify",
        json={
            "challenge": pending["challenge"],
            "code": mfa.hotp(setup["secret"], 1_000_030 // 30),
        },
    )
    assert result.status_code == 200
    client.headers["Authorization"] = "Bearer " + result.json()["access_token"]
    pending = await challenge(client)
    changed = await client.post(
        "/api/auth/password",
        json={"current_password": PASSWORD, "password": "replacement-password-123"},
    )
    assert changed.status_code == 204
    assert (
        await client.post(
            "/api/auth/mfa/verify",
            json={"challenge": pending["challenge"], "code": initial["recovery_codes"][1]},
        )
    ).status_code == 401


async def test_recent_password_and_factor_replacement_revokes_sessions(
    client, application, monkeypatch
):
    _, setup, initial = await enrolled(client, application, monkeypatch)
    assert (await client.post("/api/auth/mfa/confirm", json={"code": "123456"})).status_code == 400
    assert (
        await client.post(
            "/api/auth/mfa/replace",
            json={"current_password": "wrong", "code": initial["recovery_codes"][0]},
        )
    ).status_code == 401
    assert (
        await client.post(
            "/api/auth/mfa/replace", json={"current_password": PASSWORD, "code": "wrong"}
        )
    ).status_code == 401
    begin = await client.post(
        "/api/auth/mfa/replace",
        json={"current_password": PASSWORD, "code": initial["recovery_codes"][0]},
    )
    assert begin.status_code == 200
    replacement = begin.json()
    assert replacement["secret"] != setup["secret"]
    assert (await client.post("/api/auth/mfa/confirm", json={"code": "wrong"})).status_code == 401
    done = await client.post(
        "/api/auth/mfa/confirm", json={"code": mfa.hotp(replacement["secret"], 1_000_000 // 30)}
    )
    assert done.status_code == 200 and len(done.json()["recovery_codes"]) == 10
    assert (await client.get("/api/auth/me")).status_code == 401
    pending = await challenge(client)
    old = await client.post(
        "/api/auth/mfa/verify",
        json={"challenge": pending["challenge"], "code": initial["recovery_codes"][1]},
    )
    assert old.status_code == 401
    good = await client.post(
        "/api/auth/mfa/verify",
        json={"challenge": pending["challenge"], "code": done.json()["recovery_codes"][0]},
    )
    assert good.status_code == 200


async def test_optional_user_enrollment_expiry_and_foreign_recovery(
    client, application, monkeypatch
):
    user = await signup(client)
    enable(application)
    assert (await client.get("/api/auth/mfa")).json() == {"enrolled": False}
    # An ordinary user may enroll using a recent password without an old factor.
    setup = await client.post("/api/auth/mfa/replace", json={"current_password": PASSWORD})
    assert setup.status_code == 200
    async with application.state.factory() as db:
        row = await db.get(User, user["id"])
        row.mfa_pending_expires_at = now() - 1
        await db.commit()
    assert (await client.post("/api/auth/mfa/confirm", json={"code": "123456"})).status_code == 400
    setup = (await client.post("/api/auth/mfa/replace", json={"current_password": PASSWORD})).json()
    code = mfa.hotp(setup["secret"], int(now() // 30))
    done = await client.post("/api/auth/mfa/confirm", json={"code": code})
    assert done.status_code == 200
    pending, _, _ = await enrolled(client, application, monkeypatch)
    pending = await challenge(client)
    assert (
        await client.post(
            "/api/auth/mfa/verify",
            json={"challenge": pending["challenge"], "code": done.json()["recovery_codes"][0]},
        )
    ).status_code == 401


async def test_challenge_without_setup_or_disabled_account_cannot_authenticate(client, application):
    enable(application)
    pending = await challenge(client)
    assert (
        await client.post(
            "/api/auth/mfa/verify", json={"challenge": pending["challenge"], "code": "123456"}
        )
    ).status_code == 401
    async with application.state.factory() as db:
        row = await db.scalar(select(User).where(User.role == "admin"))
        row.active = False
        await db.commit()
    assert (
        await client.post("/api/auth/mfa/enroll", json={"challenge": pending["challenge"]})
    ).status_code == 401
