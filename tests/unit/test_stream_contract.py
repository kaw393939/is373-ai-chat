import json

import httpx
import pytest

from app.config import Settings
from app.providers import HTTPProvider, StreamEnd, TextDelta, TokenUsage

REAL_CLIENT = httpx.AsyncClient


def transport(monkeypatch, body):
    monkeypatch.setattr(
        "app.providers.httpx.AsyncClient",
        lambda **kw: REAL_CLIENT(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body)), **kw
        ),
    )


def wire(events):
    return "".join("data: " + json.dumps(event) + "\n\n" for event in events)


@pytest.mark.parametrize("provider", ["openai", "compatible"])
@pytest.mark.parametrize(
    "prefix", [[], [{"type": "response.output_text.delta", "delta": "partial"}]]
)
async def test_eof_is_never_success(monkeypatch, provider, prefix):
    if provider == "compatible" and prefix:
        prefix = [{"choices": [{"delta": {"content": "partial"}}]}]
    transport(monkeypatch, wire(prefix))
    emitted = []
    with pytest.raises(RuntimeError, match="terminal"):
        async for event in HTTPProvider(Settings(provider=provider, openai_api_key="fake")).stream(
            [], 64
        ):
            emitted.append(event)
    assert emitted == ([TextDelta("partial")] if prefix else [])


@pytest.mark.parametrize(
    "provider,events,status",
    [
        ("openai", [{"type": "response.completed", "response": {"incomplete_details": None}}], "complete"),
        (
            "openai",
            [
                {
                    "type": "response.incomplete",
                    "response": {"incomplete_details": {"reason": "max_output_tokens"}},
                }
            ],
            "incomplete",
        ),
        (
            "openai",
            [
                {
                    "type": "response.incomplete",
                    "response": {"incomplete_details": {"reason": "content_filter"}},
                }
            ],
            "refused",
        ),
        (
            "openai",
            [
                {"type": "response.refusal.delta", "delta": "Cannot comply"},
                {"type": "response.completed", "response": {"usage": None}},
            ],
            "refused",
        ),
        ("compatible", [{"choices": [{"finish_reason": "length"}]}], "incomplete"),
        ("compatible", [{"choices": [{"finish_reason": "content_filter"}]}], "refused"),
        (
            "compatible",
            [{"choices": [{"delta": {"refusal": "No"}}]}, {"choices": [{"finish_reason": "stop"}]}],
            "refused",
        ),
        (
            "compatible",
            [
                {"choices": [{"finish_reason": "stop"}]},
                {"choices": [], "usage": {"total_tokens": 3}},
            ],
            "complete",
        ),
    ],
)
async def test_terminal_reason_and_optional_usage(monkeypatch, provider, events, status):
    transport(monkeypatch, wire(events))
    result = [
        event
        async for event in HTTPProvider(Settings(provider=provider, openai_api_key="fake")).stream(
            [], 64
        )
    ]
    assert result[-1] == StreamEnd(status)
    if events[-1].get("usage"):
        assert result[-2] == TokenUsage(3)


@pytest.mark.parametrize(
    "provider,events",
    [
        ("openai", [[]]),
        ("openai", [{"error": {"message": "private upstream failure"}}]),
        ("openai", [{"type": "response.output_text.delta", "delta": 12}]),
        ("openai", [{"type": "response.completed", "response": []}]),
        ("openai", [{"type": "response.completed", "response": {"status": "failed"}}]),
        ("openai", [{"type": "response.completed", "response": {"usage": {"total_tokens": -1}}}]),
        (
            "openai",
            [
                {"type": "response.completed", "response": {}},
                {"type": "response.completed", "response": {}},
            ],
        ),
        (
            "openai",
            [
                {"type": "response.completed", "response": {}},
                {"type": "response.output_text.delta", "delta": "late"},
            ],
        ),
        ("compatible", [{"choices": "not a list"}]),
        ("compatible", [{"choices": [{}, {}]}]),
        ("compatible", [{"choices": [None]}]),
        ("compatible", [{"choices": [{"delta": []}]}]),
        ("compatible", [{"choices": [{"delta": {"tool_calls": [{}]}}]}]),
        ("compatible", [{"choices": [{"delta": {"function_call": {"name": "unsupported"}}}]}]),
        ("compatible", [{"choices": [{"delta": {"content": 5}}]}]),
        ("compatible", [{"choices": [{"finish_reason": "tool_calls"}]}]),
        (
            "compatible",
            [{"choices": [{"finish_reason": "stop"}]}, {"choices": [{"finish_reason": "stop"}]}],
        ),
        (
            "compatible",
            [
                {"choices": [{"finish_reason": "stop"}]},
                {"choices": [{"delta": {"content": "late"}}]},
            ],
        ),
    ],
)
async def test_malformed_or_unsupported_wire_is_rejected(monkeypatch, provider, events):
    transport(monkeypatch, wire(events))
    with pytest.raises((RuntimeError, ValueError)):
        _ = [
            event
            async for event in HTTPProvider(
                Settings(provider=provider, openai_api_key="fake")
            ).stream([], 64)
        ]


async def test_multiline_frame_and_incomplete_json(monkeypatch):
    transport(
        monkeypatch,
        ': heartbeat\n\nevent: response.completed\ndata: {"type":"response.completed",\ndata: "response":{}}',
    )
    assert [
        event
        async for event in HTTPProvider(Settings(provider="openai", openai_api_key="fake")).stream(
            [], 64
        )
    ] == [StreamEnd("complete")]
    transport(monkeypatch, 'data: {"type":')
    with pytest.raises(ValueError):
        _ = [
            event
            async for event in HTTPProvider(
                Settings(provider="openai", openai_api_key="fake")
            ).stream([], 64)
        ]
