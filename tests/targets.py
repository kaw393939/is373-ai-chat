"""Fail closed before a test can migrate, reset or write to an external target.

Naming is only one check. PostgreSQL also needs a loopback address and an exact
reset acknowledgement; browser writes require a nonce from the test-only server.
Remote targets are deliberately unsupported. See book/labs/README.md.
"""

import hmac
import re
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from sqlalchemy.engine import make_url

LOOPBACK = {"localhost", "127.0.0.1", "::1"}


def disposable_database(value, temporary_root=None, acknowledgement=None):
    url = make_url(value)
    if url.drivername == "sqlite+aiosqlite" and temporary_root is not None:
        path = Path(url.database or "").resolve()
        root = Path(temporary_root).resolve()
        if path.is_relative_to(root) and path != root and not url.query:
            return value
    if (
        url.drivername == "postgresql+asyncpg"
        and url.host in LOOPBACK
        and re.fullmatch(r"[a-z][a-z0-9_]*_test", url.database or "")
        and acknowledgement == url.database
        and not url.query
    ):
        return value
    raise ValueError(
        "Refusing test target: use temporary SQLite or loopback PostgreSQL with a "
        "*_test database and TEST_ALLOW_RESET equal to its name. Remote targets are unsupported."
    )


def browser_url(value):
    url = urlsplit(value)
    if (
        url.scheme != "http"
        or url.hostname not in LOOPBACK
        or url.port != 9001
        or url.username is not None
        or url.password is not None
        or url.path not in {"", "/"}
        or url.query
        or url.fragment
    ):
        raise ValueError(
            "Refusing browser target: use the disposable loopback harness on port 9001"
        )
    return value.rstrip("/")


def verify_browser_target(value, token):
    target = browser_url(value)  # Validate before constructing any network client.
    if not re.fullmatch(r"[0-9a-f]{64}", token or ""):
        raise ValueError("Browser lab requires the E2E_TARGET_TOKEN supplied by its harness")
    with httpx.Client(trust_env=False, follow_redirects=False, timeout=3) as client:
        response = client.get(target + "/_workshop/identity")
        response.raise_for_status()
        identity = response.json()
    if (
        not hmac.compare_digest(str(identity.get("token", "")), token)
        or identity.get("provider") != "mock"
        or identity.get("email") != "disabled"
        or identity.get("disposable") is not True
    ):
        raise ValueError("Browser server did not prove disposable mock identity; refusing writes")
    return target
