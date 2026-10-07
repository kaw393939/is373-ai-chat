import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.config import Settings
from app.providers import HTTPProvider, StreamEnd, TextDelta, TokenUsage


@pytest.mark.parametrize(
    "values",
    [
        {},
        {
            "openai_api_key": "test",
            "provider_expires_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        },
    ],
)
async def test_missing_or_expired_credentials(values):
    provider = HTTPProvider(Settings(provider="openai", **values))
    with pytest.raises(RuntimeError):
        _ = [e async for e in provider.stream([], 64)]


@pytest.mark.parametrize("provider", ["openai", "compatible"])
async def test_http_stream_normalization(monkeypatch, provider):
    real = httpx.AsyncClient

    def handler(request):
        payload = json.loads(request.content)
        assert payload["stream"] and request.headers["authorization"] == "Bearer test"
        if provider == "openai":
            assert payload["store"] is False
            events = [
                {"type": "response.created"},
                {"type": "response.output_text.delta", "delta": "hello"},
                {"type": "response.completed", "response": {"usage": {"total_tokens": 12}}},
            ]
        else:
            events = [
                {"choices": [{"delta": {"role": "assistant"}}]},
                {"choices": [{"delta": {"content": "hello"}}]},
                {"choices": [{"delta": {}, "finish_reason": "stop"}]},
                {"usage": {"total_tokens": 12}},
            ]
        stream = (
            ": heartbeat\n\n"
            + "".join("data: " + json.dumps(e) + "\n\n" for e in events)
            + "data: [DONE]\n\n"
        )
        return httpx.Response(200, text=stream)

    monkeypatch.setattr(
        "app.providers.httpx.AsyncClient",
        lambda **kw: real(transport=httpx.MockTransport(handler), **kw),
    )
    events = [
        e
        async for e in HTTPProvider(Settings(provider=provider, openai_api_key="test")).stream(
            [{"role": "user", "content": "test"}], 64
        )
    ]
    assert events == [TextDelta("hello"), TokenUsage(12), StreamEnd("complete")]


@pytest.mark.parametrize("kind", ["error", "response.failed", "response.incomplete"])
async def test_provider_failure(monkeypatch, kind):
    real = httpx.AsyncClient
    monkeypatch.setattr(
        "app.providers.httpx.AsyncClient",
        lambda **kw: real(
            transport=httpx.MockTransport(
                lambda r: httpx.Response(200, text="data: " + json.dumps({"type": kind}) + "\n\n")
            ),
            **kw,
        ),
    )
    with pytest.raises(RuntimeError):
        _ = [
            e
            async for e in HTTPProvider(Settings(provider="openai", openai_api_key="test")).stream(
                [], 64
            )
        ]
