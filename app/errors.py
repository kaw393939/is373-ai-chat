"""Use cases report domain failures; the HTTP adapter chooses status codes."""

from enum import StrEnum


class Failure(StrEnum):
    INVALID = "invalid"
    UNAUTHENTICATED = "unauthenticated"
    FORBIDDEN = "forbidden"
    MISSING = "missing"
    CONFLICT = "conflict"
    TOO_LARGE = "too_large"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"


class DomainError(Exception):
    def __init__(self, kind: Failure, detail: str):
        self.kind, self.detail = kind, detail
        super().__init__(detail)
