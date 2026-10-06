"""Adapters keep HTTP/SSE and vendor objects outside application policies."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Protocol

import httpx


class Provider(Protocol):
    def stream(self, messages, max_output): ...


class MockProvider:
    async def stream(self, messages, max_output):
        text = "Workshop reply: " + messages[-1]["content"]
        for word in text[:max_output].split():
            await asyncio.sleep(0.025)
            yield {"text": word + " "}
        yield {"tokens": len(text.split())}


class HTTPProvider:
    def __init__(self, config):
        self.config = config

    async def stream(self, messages, max_output):
        config = self.config
        if config.provider_expires_at and datetime.now(timezone.utc) >= datetime.fromisoformat(
            config.provider_expires_at
        ):
            raise RuntimeError("Provider credential lease has expired")
        if not config.openai_api_key:
            raise RuntimeError("Provider is not configured")
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
            }
        )
        endpoint = "/responses" if responses else "/chat/completions"
        async with httpx.AsyncClient(timeout=httpx.Timeout(120, connect=10)) as client:
            async with client.stream(
                "POST",
                config.provider_base_url.rstrip("/") + endpoint,
                headers={"Authorization": f"Bearer {config.openai_api_key}"},
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:") or line[5:].strip() == "[DONE]":
                        continue
                    event = json.loads(line[5:])
                    if responses:
                        if event.get("type") == "response.output_text.delta":
                            yield {"text": event["delta"]}
                        elif event.get("type") == "response.completed":
                            yield {"tokens": event["response"]["usage"]["total_tokens"]}
                        elif event.get("type") in {
                            "error",
                            "response.failed",
                            "response.incomplete",
                        }:
                            raise RuntimeError("Provider could not complete the response")
                    else:
                        for choice in event.get("choices", []):
                            if choice.get("delta", {}).get("content"):
                                yield {"text": choice["delta"]["content"]}
                        if event.get("usage"):
                            yield {"tokens": event["usage"]["total_tokens"]}


def make_provider(config):
    return MockProvider() if config.provider == "mock" else HTTPProvider(config)
