"""Password-bound MFA challenges, encrypted factors and single-use recovery.

A challenge is an opaque, five-minute restricted credential, never an app JWT.
The user row serializes factor/recovery consumption across workers. RFC6238
supplies the time-based algorithm; enrollment and recovery are app policy.
"""

import base64
import hashlib
import hmac
import secrets
import struct
from urllib.parse import quote, urlencode

from cryptography.fernet import Fernet
from fastapi import HTTPException
from sqlalchemy import delete

from app.models import Audit, MfaChallenge, MfaRecovery, User, now
from app.security import digest, secret_token
from app.services import revoke_all


def hotp(secret, counter):
    key = base64.b32decode(secret)
    mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = mac[-1] & 15
    value = int.from_bytes(mac[offset : offset + 4], "big") & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


def valid_counter(secret, code, instant, last=-1):
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        return None
    current = int(instant // 30)
    # A narrow skew window admits adjacent time steps, but never an already
    # accepted counter. A recorded counter makes a successful OTP one-use.
    for counter in range(max(0, current - 1), current + 2):
        if counter > last and hmac.compare_digest(hotp(secret, counter), code):
            return counter
    return None


def cipher(config):
    if not config.mfa_encryption_key:
        raise HTTPException(503, "MFA configuration is unavailable; contact the administrator")
    return Fernet(config.mfa_encryption_key.encode())


def setup_secret(config, user, encrypted=None):
    box = cipher(config)
    secret = (
        box.decrypt(encrypted.encode()).decode()
        if encrypted
        else base64.b32encode(secrets.token_bytes(20)).decode()
    )
    uri = (
        "otpauth://totp/"
        + quote("Firehose360:" + user.email, safe="")
        + "?"
        + urlencode(
            {
                "secret": secret,
                "issuer": "Firehose360",
                "algorithm": "SHA1",
                "digits": 6,
                "period": 30,
            }
        )
    )
    return secret, box.encrypt(secret.encode()).decode(), {"secret": secret, "otpauth_url": uri}


async def password_challenge(db, user):
    # The password was verified immediately before this restricted credential.
    await db.refresh(user, with_for_update=True)
    await db.execute(delete(MfaChallenge).where(MfaChallenge.user_id == user.id))
    value = secret_token()
    db.add(MfaChallenge(digest=digest(value), user_id=user.id, expires_at=now() + 300))
    await db.commit()
    return {
        "mfa_required": True,
        "challenge": value,
        "enrollment_required": not bool(user.mfa_secret),
    }


async def locked_challenge(db, value):
    candidate = await db.get(MfaChallenge, digest(value))
    if not candidate:
        raise HTTPException(401, "Invalid or expired MFA challenge")
    user = await db.get(User, candidate.user_id, with_for_update=True)
    await db.refresh(candidate, with_for_update=True)
    if (
        candidate.used
        or candidate.expires_at <= now()
        or candidate.attempts >= 5
        or not (user.active and user.approved and user.email_verified)
    ):
        raise HTTPException(401, "Invalid or expired MFA challenge")
    return user, candidate


async def enroll_challenge(db, value, config):
    user, challenge = await locked_challenge(db, value)
    if user.mfa_secret:
        raise HTTPException(400, "MFA is already enrolled")
    _, encrypted, view = setup_secret(config, user, challenge.enrollment_secret)
    challenge.enrollment_secret = encrypted
    await db.commit()
    return view


async def recovery_codes(db, user):
    await db.execute(delete(MfaRecovery).where(MfaRecovery.user_id == user.id))
    values = [secrets.token_hex(16) for _ in range(10)]
    db.add_all([MfaRecovery(digest=digest(value), user_id=user.id) for value in values])
    return values


async def consume_factor(db, user, code, config):
    if not user.mfa_secret:
        return False
    secret = cipher(config).decrypt(user.mfa_secret.encode()).decode()
    counter = valid_counter(secret, code, now(), user.mfa_last_counter)
    if counter is not None:
        user.mfa_last_counter = counter
        return True
    recovery = await db.get(MfaRecovery, digest(code.strip().lower()))
    if not recovery or recovery.user_id != user.id or recovery.used:
        return False
    recovery.used = True
    db.add(Audit(actor_id=user.id, action="mfa.recovery.used", target_id=user.id))
    return True


async def verify_challenge(db, value, code, config):
    user, challenge = await locked_challenge(db, value)
    codes = None
    if not user.mfa_secret and challenge.enrollment_secret:
        secret = cipher(config).decrypt(challenge.enrollment_secret.encode()).decode()
        counter = valid_counter(secret, code, now())
        valid = counter is not None
        if valid:
            user.mfa_secret, user.mfa_last_counter = challenge.enrollment_secret, counter
            codes = await recovery_codes(db, user)
            await revoke_all(db, user.id)
            db.add(Audit(actor_id=user.id, action="mfa.enrolled", target_id=user.id))
    else:
        valid = await consume_factor(db, user, code, config)
    if not valid:
        challenge.attempts += 1
        await db.commit()  # Rejected guesses consume the challenge's durable budget.
        raise HTTPException(401, "Invalid MFA code")
    challenge.used = True
    return user, codes  # The route's new_session commits factor + session together.


async def begin_replacement(db, user, code, config):
    await db.refresh(user, with_for_update=True)
    if user.mfa_secret and not await consume_factor(db, user, code, config):
        raise HTTPException(401, "Invalid MFA code")
    _, encrypted, view = setup_secret(config, user)
    user.mfa_pending_secret, user.mfa_pending_expires_at = encrypted, now() + 300
    await db.commit()
    return view


async def confirm_replacement(db, user, code, config):
    await db.refresh(user, with_for_update=True)
    if not user.mfa_pending_secret or user.mfa_pending_expires_at <= now():
        raise HTTPException(400, "MFA setup expired; verify your password again")
    secret = cipher(config).decrypt(user.mfa_pending_secret.encode()).decode()
    counter = valid_counter(secret, code, now())
    if counter is None:
        raise HTTPException(401, "Invalid MFA code")
    user.mfa_secret, user.mfa_last_counter = user.mfa_pending_secret, counter
    user.mfa_pending_secret, user.mfa_pending_expires_at = None, None
    codes = await recovery_codes(db, user)
    await revoke_all(db, user.id)
    db.add(Audit(actor_id=user.id, action="mfa.replaced", target_id=user.id))
    await db.commit()
    return {"recovery_codes": codes}
