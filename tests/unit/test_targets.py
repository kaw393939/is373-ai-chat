import httpx
import pytest

from tests import conftest
from tests.targets import disposable_database, verify_browser_target


@pytest.mark.parametrize(
    "url,ack",
    [
        ("postgresql+asyncpg://u:p@firehose360.com/chat_test", "chat_test"),
        ("postgresql+asyncpg://u:p@127.0.0.1/production", "production"),
        ("postgresql+asyncpg://u:p@127.0.0.1/chat_test", None),
        ("postgresql+asyncpg://u:p@127.0.0.1/chat_test?host=firehose360.com", "chat_test"),
        ("sqlite+aiosqlite:///./.state/local.db", None),
    ],
)
def test_database_refuses_unsafe_target(url, ack, tmp_path):
    with pytest.raises(ValueError, match="Refusing test target"):
        disposable_database(url, tmp_path, ack)


async def test_fixture_refuses_before_migration_or_application(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setenv("TEST_DATABASE_URL", "postgresql+asyncpg://u:p@firehose360.com/chat_test")
    monkeypatch.setenv("TEST_ALLOW_RESET", "chat_test")
    monkeypatch.setattr(conftest.subprocess, "run", lambda *a, **k: calls.append("migration"))
    monkeypatch.setattr(conftest, "create_app", lambda *a, **k: calls.append("application"))
    fixture = conftest.application.__wrapped__(tmp_path)
    with pytest.raises(ValueError, match="Refusing test target"):
        await anext(fixture)
    assert calls == []


@pytest.mark.parametrize(
    "url",
    [
        "https://firehose360.com",
        "http://dev.firehose360.com:9001",
        "http://localhost:9001@firehose360.com",
        "http://127.0.0.1:9001/?redirect=production",
        "http://127.0.0.1:8000",
    ],
)
def test_browser_refuses_before_network(monkeypatch, url):
    calls = []
    monkeypatch.setattr(httpx, "Client", lambda **k: calls.append("network"))
    with pytest.raises(ValueError, match="Refusing browser target"):
        verify_browser_target(url, "a" * 64)
    assert calls == []


def test_safe_database_and_browser_identity(monkeypatch, tmp_path):
    assert disposable_database(f"sqlite+aiosqlite:///{tmp_path}/test.db", tmp_path)
    assert disposable_database("postgresql+asyncpg://u:p@127.0.0.1/chat_test", None, "chat_test")
    token = "a" * 64
    identity = {"token": token, "provider": "mock", "email": "disabled", "disposable": True}
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=identity))
    original = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original(transport=transport, **kwargs))
    assert verify_browser_target("http://localhost:9001", token) == "http://localhost:9001"
    identity["token"] = "b" * 64
    with pytest.raises(ValueError, match="did not prove"):
        verify_browser_target("http://localhost:9001", token)
    identity["token"] = token
    identity["provider"] = "openai"
    with pytest.raises(ValueError, match="did not prove"):
        verify_browser_target("http://localhost:9001", token)
    with pytest.raises(ValueError, match="E2E_TARGET_TOKEN"):
        verify_browser_target("http://localhost:9001", None)
