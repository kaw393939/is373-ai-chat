import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import HTTPException

hasher = PasswordHasher(time_cost=3, memory_cost=32768, parallelism=1)
DUMMY_HASH = hasher.hash("unused-constant-for-missing-account")


def digest(value):
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
    try:
        return jwt.decode(
            token,
            config.jwt_secret,
            algorithms=["HS256"],
            issuer=config.base_url,
            audience="373-chat",
            options={"require": ["sub", "sid", "iss", "aud", "exp", "iat"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Invalid or expired session") from exc
