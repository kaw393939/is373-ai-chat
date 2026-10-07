"""Typed generation states and app notifications, independent of HTTP/SSE."""

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from app.providers import StreamStatus


class GenerationState(StrEnum):
    STREAMING = "streaming"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    REFUSED = "refused"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


def provider_outcome(status: StreamStatus) -> GenerationState:
    # Only these provider outcomes may certify a terminal provider result.
    return {
        "complete": GenerationState.COMPLETE,
        "incomplete": GenerationState.INCOMPLETE,
        "refused": GenerationState.REFUSED,
    }[status]


@dataclass(frozen=True, slots=True)
class Started:
    kind: ClassVar[str] = "started"
    run_id: str
    message_id: str


@dataclass(frozen=True, slots=True)
class Delta:
    kind: ClassVar[str] = "delta"
    text: str


@dataclass(frozen=True, slots=True)
class Error:
    kind: ClassVar[str] = "error"
    message: str


@dataclass(frozen=True, slots=True)
class Completed:
    kind: ClassVar[str] = "completed"
    status: GenerationState
    tokens: int | None


AppEvent = Started | Delta | Error | Completed
