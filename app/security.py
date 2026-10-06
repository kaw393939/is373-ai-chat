"""Validate identity claims; routes/services still enforce current authority.

Passwords, opaque bearer tokens and signed JWTs have different threat models.
See book/04-auth.md and book/labs/01-token-boundaries.md for the worked tour.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import HTTPException

hasher = PasswordHasher(time_cost=3, memory_cost=32768, parallelism=1)
# Missing accounts still perform an expensive verification in the login path.
# This reduces a timing difference; it is not a claim of constant-time login.
DUMMY_HASH = hasher.hash("unused-constant-for-missing-account")


def digest(value):
    """Index high-entropy refresh/recovery secrets without storing bearer values.

    Fast SHA-256 is suitable here because secret_token supplies randomness.
    Human-chosen passwords instead use the expensive Argon2 functions below.
    """
    return hashlib.sha256(value.encode()).hexdigest()


def secret_token():
    return secrets.token_urlsafe(48)


def hash_password(value):
    return hasher.hash(value)


def verify_password(value, hashed):
    try:
        return hasher.verify(hashed, value)
    except (VerificationError, InvalidHashError):
        return False


def access_token(user_id, family_id, config):
    # A signature authenticates readable claims; it does not encrypt the payload.
    # The family identifier lets current() consult durable revocation state.
    instant = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "sid": family_id,
            "iss": config.base_url,
            "aud": "373-chat",
            "iat": instant,
            "exp": instant + timedelta(minutes=config.access_minutes),
        },
        config.jwt_secret,
        algorithm="HS256",
    )


def decode_token(token, config):
    """Reject invalid claims; success alone does not authorize an app action."""
    try:
        return jwt.decode(
            token,
            config.jwt_secret,
            # Server policy selects the algorithm, not the token's own header.
            algorithms=["HS256"],
            issuer=config.base_url,
            audience="373-chat",
            options={"require": ["sub", "sid", "iss", "aud", "exp", "iat"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Invalid or expired session") from exc
