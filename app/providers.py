"""Normalize vendor framing into text, usage and an explicit terminal outcome.

The domain never infers success from EOF. See book/05-streaming.md: substitutable
adapters preserve completion semantics as well as a common method signature.
"""

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Protocol, TypedDict

import httpx
from pydantic import BaseModel, Field


class ChatMessage(TypedDict):
    role: str
    content: str


StreamStatus = Literal["complete", "incomplete", "refused"]


@dataclass(frozen=True, slots=True)
class TextDelta:
    text: str


@dataclass(frozen=True, slots=True)
class TokenUsage:
    tokens: int


@dataclass(frozen=True, slots=True)
class StreamEnd:
    status: StreamStatus


ProviderEvent = TextDelta | TokenUsage | StreamEnd


class Provider(Protocol):
    def stream(
        self, messages: list[ChatMessage], max_output: int
    ) -> AsyncIterator[ProviderEvent]: ...


class UsagePayload(BaseModel):
    total_tokens: int = Field(ge=0, strict=True)


class DeltaPayload(BaseModel):
    delta: str = Field(strict=True)


class ProviderStreamError(RuntimeError):
    """A generic protocol failure; do not include private vendor payloads."""


class MockProvider:
    async def stream(
        self, messages: list[ChatMessage], max_output: int
    ) -> AsyncIterator[ProviderEvent]:
        text = "Workshop reply: " + messages[-1]["content"]
        for word in text[:max_output].split():
            await asyncio.sleep(0.025)
            yield TextDelta(word + " ")
        yield TokenUsage(len(text.split()))
        yield StreamEnd("complete")


async def data_frames(response: httpx.Response) -> AsyncIterator[str]:
    """SSE data may span lines; transport chunks/heartbeats are not JSON events."""
    pending: list[str] = []
    async for line in response.aiter_lines():
        if line.startswith("data:"):
            pending.append(line[5:].lstrip())
        elif not line and pending:
            yield "\n".join(pending)
            pending = []
    if pending:
        yield "\n".join(pending)


class HTTPProvider:
    def __init__(self, config):
        self.config = config

    async def stream(
        self, messages: list[ChatMessage], max_output: int
    ) -> AsyncIterator[ProviderEvent]:
        config = self.config
        if config.provider_expires_at and datetime.now(timezone.utc) >= datetime.fromisoformat(
            config.provider_expires_at
        ):
            raise ProviderStreamError("Provider credential lease has expired")
        if not config.openai_api_key:
            raise ProviderStreamError("Provider is not configured")
        responses = config.provider == "openai"
        payload = (
            {
                "model": config.provider_model,
                "input": messages,
                "store": False,
                "max_output_tokens": max_output,
                "stream": True,
            }
            if responses
            else {
                "model": config.provider_model,
                "messages": messages,
                "max_tokens": max_output,
                "stream": True,
                "stream_options": {"include_usage": True},
                "n": 1,
            }
        )
        endpoint = "/responses" if responses else "/chat/completions"
        terminal: StreamStatus | None = None
        refused = False
        async with httpx.AsyncClient(timeout=httpx.Timeout(120, connect=10)) as client:
            async with client.stream(
                "POST",
                config.provider_base_url.rstrip("/") + endpoint,
                headers={"Authorization": "Bearer " + config.openai_api_key},
                json=payload,
            ) as response:
                response.raise_for_status()
                async for frame in data_frames(response):
                    if frame.strip() == "[DONE]":
                        break
                    event = json.loads(frame)
                    if not isinstance(event, dict):
                        raise ProviderStreamError("Malformed provider event")
                    if "error" in event:
                        raise ProviderStreamError("Provider reported an error")
                    if responses:
                        kind = event.get("type")
                        if kind in {"response.output_text.delta", "response.refusal.delta"}:
                            if terminal:
                                raise ProviderStreamError("Output followed terminal event")
                            refused |= kind == "response.refusal.delta"
                            yield TextDelta(DeltaPayload.model_validate(event).delta)
                        elif kind in {"response.completed", "response.incomplete"}:
                            if terminal or not isinstance(event.get("response"), dict):
                                raise ProviderStreamError("Malformed terminal event")
                            result = event["response"]
                            if (
                                kind == "response.completed"
                                and result.get("status", "completed") != "completed"
                            ):
                                raise ProviderStreamError("Inconsistent terminal status")
                            usage = result.get("usage")
                            if usage is not None:
                                yield TokenUsage(UsagePayload.model_validate(usage).total_tokens)
                            terminal = (
                                "refused"
                                if refused
                                or (result.get("incomplete_details") or {}).get("reason")
                                == "content_filter"
                                else "complete"
                                if kind == "response.completed"
                                else "incomplete"
                            )
                        elif kind in {"error", "response.failed"}:
                            raise ProviderStreamError("Provider could not complete response")
                    else:
                        choices = event.get("choices", [])
                        if not isinstance(choices, list) or len(choices) > 1:
                            raise ProviderStreamError("Unsupported provider choices")
                        for choice in choices:
                            if not isinstance(choice, dict) or not isinstance(
                                choice.get("delta", {}), dict
                            ):
                                raise ProviderStreamError("Malformed provider choice")
                            delta = choice.get("delta", {})
                            if delta.get("tool_calls") or delta.get("function_call"):
                                raise ProviderStreamError("Tool calls are not supported")
                            if delta.get("content") is not None:
                                if terminal or not isinstance(delta["content"], str):
                                    raise ProviderStreamError("Malformed text delta")
                                yield TextDelta(delta["content"])
                            refused |= bool(delta.get("refusal"))
                            reason = choice.get("finish_reason")
                            if reason is not None:
                                if terminal or reason not in {"stop", "length", "content_filter"}:
                                    raise ProviderStreamError("Unsupported terminal reason")
                                terminal = (
                                    "incomplete"
                                    if reason == "length"
                                    else "refused"
                                    if refused or reason == "content_filter"
                                    else "complete"
                                )
                        usage = event.get("usage")
                        if usage is not None:
                            yield TokenUsage(UsagePayload.model_validate(usage).total_tokens)
        if terminal is None:
            raise ProviderStreamError("Provider stream ended before a terminal event")
        yield StreamEnd(terminal)


def make_provider(config) -> Provider:
    return MockProvider() if config.provider == "mock" else HTTPProvider(config)
