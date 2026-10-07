import base64
import json

import pytest

from app.errors import DomainError
from app.pagination import decode_cursor, signature


@pytest.mark.parametrize(
    "value", [[True, "x"], [None, "x"], [float("inf"), "x"], [1, None], [1, "x" * 37], [1]]
)
def test_signed_but_malformed_cursor(value):
    body = base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")
    with pytest.raises(DomainError):
        decode_cursor(body + "." + signature(body, "scope", "secret"), "scope", "secret")
