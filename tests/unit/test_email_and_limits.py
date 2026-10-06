import httpx
import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError

from app.config import Settings
from app.email import ResendMailer, make_mailer
from app.middleware import BodyLimit


def test_email_configuration():
    for values in [
        {"email_provider": "invalid"},
        {"email_provider": "mock"},
        {"email_provider": "resend", "email_encryption_key": Fernet.generate_key().decode()},
    ]:
        with pytest.raises((ValidationError, ValueError)):
            Settings(**values)
    config = Settings(
        email_provider="resend",
        resend_api_key="test-only",
        email_encryption_key=Fernet.generate_key().decode(),
    )
    assert isinstance(make_mailer(config), ResendMailer)
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            email_provider="mock",
            email_encryption_key=Fernet.generate_key().decode(),
        )


async def test_resend_https_contract(monkeypatch):
    def handler(request):
        assert request.url == "https://api.resend.com/emails"
        assert request.headers["Authorization"] == "Bearer test-only"
        assert request.headers["Idempotency-Key"] == "same-message"
        return httpx.Response(200, json={"id": "provider-message"})

    original = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )
    mailer = ResendMailer(Settings(resend_api_key="test-only"))
    assert await mailer.send({"text": "Test"}, "same-message") == "provider-message"


async def test_local_sqlite_email_delivery(tmp_path):
    from app.db import database
    from app.email import drain, enqueue
    from app.models import Base, RoleBudget

    engine, factory = database(f"sqlite+aiosqlite:///{tmp_path}/email.db")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    config = Settings(email_provider="mock", email_encryption_key=Fernet.generate_key().decode())
    mailer = make_mailer(config)
    async with factory() as db:
        db.add(RoleBudget(role="user"))
        await db.commit()
        await enqueue(db, config, "learner@example.org", "Local email", "Local workflow")
        await db.commit()
    await drain(factory, config, mailer)
    assert mailer.messages[0]["text"] == "Local workflow"
    await engine.dispose()


async def test_body_limit_chunks_disconnect_and_non_http():
    async def downstream(scope, receive, send):
        if scope["type"] == "http":
            assert (await receive())["body"] == b"1234"
            assert (await receive())["type"] == "http.disconnect"
        await send({"type": "called"})

    middleware = BodyLimit(downstream, maximum=4)
    responses = []

    async def send(message):
        responses.append(message)

    def receiver(messages):
        async def receive():
            return messages.pop(0)

        return receive

    await middleware({"type": "websocket"}, receiver([]), send)
    assert responses.pop()["type"] == "called"
    await middleware({"type": "http"}, receiver([{"type": "http.disconnect"}]), send)
    assert not responses
    await middleware(
        {"type": "http"},
        receiver(
            [
                {"type": "http.request", "body": b"12", "more_body": True},
                {"type": "http.request", "body": b"34"},
                {"type": "http.disconnect"},
            ]
        ),
        send,
    )
    assert responses.pop()["type"] == "called"
    await middleware({"type": "http"}, receiver([{"type": "http.request", "body": b"12345"}]), send)
    assert responses[0]["status"] == 413
