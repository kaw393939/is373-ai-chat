"""Bounded keyset pages; cursors bind the caller, filter and ordering contract."""

import base64
import hashlib
import hmac
import json
import math

from sqlalchemy import and_, or_

from app.errors import DomainError, Failure


def signature(body, scope, secret):
    return hmac.new(secret.encode(), f"page:{scope}:{body}".encode(), hashlib.sha256).hexdigest()


def encode_cursor(item, scope, secret):
    body = (
        base64.urlsafe_b64encode(json.dumps([item.created_at, item.id]).encode())
        .decode()
        .rstrip("=")
    )
    return body + "." + signature(body, scope, secret)


def decode_cursor(value, scope, secret):
    try:
        body, signed = value.split(".")
        if not hmac.compare_digest(signature(body, scope, secret), signed):
            raise ValueError("signature")
        at, identifier = json.loads(
            base64.b64decode(body + "=" * (-len(body) % 4), altchars=b"-_", validate=True)
        )
        if (
            not isinstance(at, (int, float))
            or isinstance(at, bool)
            or not math.isfinite(at)
            or not isinstance(identifier, str)
            or len(identifier) > 36
        ):
            raise ValueError("shape")
        return at, identifier
    except (ValueError, TypeError):
        raise DomainError(Failure.INVALID, "Invalid page cursor") from None


async def page_rows(db, model, statement, limit, cursor, scope, secret):
    if cursor:
        at, identifier = decode_cursor(cursor, scope, secret)
        statement = statement.where(
            or_(model.created_at < at, and_(model.created_at == at, model.id < identifier))
        )
    rows = list(
        (
            await db.scalars(
                statement.order_by(model.created_at.desc(), model.id.desc()).limit(limit + 1)
            )
        ).all()
    )
    next_cursor = encode_cursor(rows[limit - 1], scope, secret) if len(rows) > limit else None
    return rows[:limit], next_cursor
