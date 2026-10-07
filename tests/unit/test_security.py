from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.config import Settings
from app.db import database
from app.providers import (
    HTTPProvider,
    MockProvider,
    StreamEnd,
    TextDelta,
    TokenUsage,
    make_provider,
)
from app.security import (
    access_token,
    decode_token,
    digest,
    hash_password,
    secret_token,
    verify_password,
)


def test_passwords_and_tokens():
    config = Settings()
    hashed = hash_password("a sufficiently long password")
    assert verify_password("a sufficiently long password", hashed)
    assert not verify_password("wrong", hashed)
    assert not verify_password("wrong", "invalid hash")
    assert digest("abc") == digest("abc") and len(digest("abc")) == 64
    assert secret_token() != secret_token()
    encoded = access_token("u", "session", config)
    assert decode_token(encoded, config)["sid"] == "session"
    for token in [
        "garbage",
        jwt.encode(
            {
                "sub": "u",
                "sid": "s",
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
                "iss": config.base_url,
                "aud": "373-chat",
            },
            config.jwt_secret,
            algorithm="HS256",
        ),
    ]:
        with pytest.raises(HTTPException):
            decode_token(token, config)


@pytest.mark.parametrize(
    "values",
    [
        {"registration_policy": "anything"},
        {"provider": "invalid"},
        {"admin_mfa_required": True},
        {"mfa_encryption_key": "invalid"},
        {"app_env": "production"},
        {"app_env": "production", "jwt_secret": "x" * 64},
        {"app_env": "production", "jwt_secret": "x" * 64, "base_url": "https://example.org"},
        {
            "app_env": "production",
            "jwt_secret": "x" * 64,
            "base_url": "https://example.org",
            "database_url": "postgresql+asyncpg://u:p@localhost/test",
            "provider_base_url": "http://example.org",
        },
    ],
)
def test_invalid_configuration(values):
    with pytest.raises(ValidationError):
        Settings(**values)


def test_production_configuration():
    config = Settings(
        app_env="production",
        jwt_secret="x" * 64,
        base_url="https://example.org",
        database_url="postgresql+asyncpg://u:p@localhost/test",
    )
    assert config.secure_cookie and not Settings().secure_cookie
    assert isinstance(make_provider(config), MockProvider)
    assert isinstance(make_provider(Settings(provider="openai")), HTTPProvider)
    engine, _ = database(config.database_url)
    assert engine.pool.size() == 5


async def test_mock_provider():
    events = [e async for e in MockProvider().stream([{"role": "user", "content": "Hello"}], 512)]
    assert "Hello" in "".join(e.text for e in events if isinstance(e, TextDelta))
    assert isinstance(events[-2], TokenUsage) and events[-2].tokens > 0
    assert events[-1] == StreamEnd("complete")


async def test_sqlite_foreign_keys():
    from sqlalchemy import text

    engine, _ = database("sqlite+aiosqlite:///:memory:")
    async with engine.connect() as connection:
        assert (await connection.execute(text("PRAGMA foreign_keys"))).scalar() == 1
    await engine.dispose()


def test_configuration_validation_does_not_echo_credentials():
    with pytest.raises(ValidationError) as rejected:
        Settings(app_env="production", mfa_encryption_key="synthetic-sensitive-key")
    assert "input_value" not in str(rejected.value)
    assert "synthetic-sensitive-key" not in str(rejected.value)
