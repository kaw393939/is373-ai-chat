"""Process fault targets are fixed loopback ports and one disposable database."""

import hmac
import re
from urllib.parse import urlsplit

from sqlalchemy.engine import make_url

from tests.targets import disposable_database

URLS = ("http://127.0.0.1:9002", "http://127.0.0.1:9003")


def process_database(value, acknowledgement):
    disposable_database(value, acknowledgement=acknowledgement)
    if make_url(value).database != "process_test":
        raise ValueError("Process experiment requires its own process_test database")
    return value


def process_url(value):
    # Exact allowlist also rejects userinfo, alternate paths, queries and HTTPS.
    if value not in URLS or urlsplit(value).hostname != "127.0.0.1":
        raise ValueError("Process experiment requires its own loopback 9002/9003 target")
    return value


def nonce(value):
    if not re.fullmatch(r"[0-9a-f]{64}", value or ""):
        raise ValueError("Process experiment requires a fresh harness nonce")
    return value


def verify_identity(value, token, number):
    nonce(token)
    if (
        not hmac.compare_digest(str(value.get("nonce", "")), token)
        or value.get("replica") != number
        or value.get("database") != "process_test"
        or value.get("provider") != "fault-mock"
        or value.get("mail") not in {"disabled", "synthetic-receipts"}
    ):
        raise ValueError("Process did not prove its disposable synthetic identity")
