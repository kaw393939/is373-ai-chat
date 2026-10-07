"""Translate application outcomes into HTTP status codes and SSE frames."""

import json
from collections.abc import AsyncGenerator
from contextlib import aclosing
from dataclasses import asdict

import anyio
from starlette.responses import StreamingResponse

from app.errors import Failure
from app.events import AppEvent

HTTP_STATUS = {
    Failure.INVALID: 400,
    Failure.UNAUTHENTICATED: 401,
    Failure.FORBIDDEN: 403,
    Failure.MISSING: 404,
    Failure.CONFLICT: 409,
    Failure.TOO_LARGE: 413,
    Failure.LIMITED: 429,
    Failure.UNAVAILABLE: 503,
}


def encode_event(event: AppEvent) -> str:
    return f"event: {event.kind}\ndata: {json.dumps(asdict(event))}\n\n"


async def encode_stream(events: AsyncGenerator[AppEvent, None]) -> AsyncGenerator[str, None]:
    async with aclosing(events):
        async for event in events:
            yield encode_event(event)


class GenerationResponse(StreamingResponse):
    """Close suspended generators even when cancellation interrupts send()."""

    async def stream_response(self, send):
        try:
            await super().stream_response(send)
        finally:
            with anyio.CancelScope(shield=True):
                await self.body_iterator.aclose()
