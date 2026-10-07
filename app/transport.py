"""Translate application outcomes into HTTP status codes and SSE frames."""

import json
from collections.abc import AsyncIterator
from dataclasses import asdict

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


async def encode_stream(events: AsyncIterator[AppEvent]) -> AsyncIterator[str]:
    async for event in events:
        yield encode_event(event)
