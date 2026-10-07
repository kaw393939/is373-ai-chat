import asyncio
from datetime import datetime, timezone

import anyio
from sqlalchemy import delete, func, select, update

from app.errors import DomainError, Failure
from app.events import Completed, Delta, Error, GenerationState, Started, provider_outcome
from app.models import (
    Audit,
    Conversation,
    DailyUsage,
    Family,
    Generation,
    Message,
    MfaChallenge,
    Recovery,
    Refresh,
    RoleBudget,
    User,
    now,
)
from app.policies import eligible_account, requires_mfa
from app.providers import StreamEnd, TextDelta, TokenUsage
from app.security import access_token, digest, secret_token


def user_view(user):
    return {
        k: getattr(user, k)
        for k in [
            "id",
            "email",
            "role",
            "active",
            "approved",
            "email_verified",
            "daily_requests",
            "daily_units",
            "max_concurrent",
        ]
    }


async def authorize_password_snapshot(session, user, verified_hash):
    # Argon2 runs outside a row lock. Fence the checked hash against current
    # durable state before minting authority or changing a sensitive factor.
    await session.refresh(user, with_for_update=True)
    if not eligible_account(user) or user.password_hash != verified_hash:
        raise DomainError(Failure.UNAUTHENTICATED, "Authentication changed; sign in again")


async def require_family(session, user, family_id, config):
    family = await session.get(Family, family_id, with_for_update=True, populate_existing=True)
    if (
        not family
        or family.user_id != user.id
        or family.revoked
        or family.expires_at <= now()
        or (requires_mfa(user, config) and not family.mfa_verified)
    ):
        raise DomainError(Failure.UNAUTHENTICATED, "Session is no longer active")
    return family


async def new_session(session, user, config, mfa_verified=False):
    family = Family(
        user_id=user.id, expires_at=now() + config.refresh_days * 86400, mfa_verified=mfa_verified
    )
    session.add(family)
    await session.flush()
    value = secret_token()
    session.add(Refresh(digest=digest(value), family_id=family.id))
    await session.commit()
    return access_token(user.id, family.id, config), value


async def rotate(session, value, config):
    # Family lock serializes rotation and reuse detection across workers.
    token = await session.get(Refresh, digest(value))
    if not token:
        raise DomainError(Failure.UNAUTHENTICATED, "Invalid refresh session")
    family = (
        await session.scalars(select(Family).where(Family.id == token.family_id).with_for_update())
    ).one()
    await session.refresh(token)
    if token.used:
        family.revoked = True
        await session.commit()
        raise DomainError(Failure.UNAUTHENTICATED, "Refresh reuse detected; sign in again")
    user = await session.get(User, family.user_id)
    if (
        family.revoked
        or family.expires_at <= now()
        or not user.active
        or not user.approved
        or not user.email_verified
        or (requires_mfa(user, config) and not family.mfa_verified)
    ):
        raise DomainError(Failure.UNAUTHENTICATED, "Session revoked or expired")
    token.used = True
    fresh = secret_token()
    session.add(Refresh(digest=digest(fresh), family_id=family.id))
    await session.commit()
    return access_token(user.id, family.id, config), fresh


async def revoke_all(session, user_id):
    await session.execute(
        update(MfaChallenge).where(MfaChallenge.user_id == user_id).values(used=True)
    )
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(mfa_pending_secret=None, mfa_pending_expires_at=None)
    )
    await session.execute(update(Family).where(Family.user_id == user_id).values(revoked=True))
    await session.execute(
        update(Generation)
        .where(Generation.user_id == user_id, Generation.status == "streaming")
        .values(cancel_requested=True)
    )


async def owned(session, conversation_id, user_id):
    # Existence and ownership share a 404 response so this lookup does not tell
    # an unrelated account which conversation identifiers exist.
    item = await session.get(Conversation, conversation_id, with_for_update=True)
    if not item or item.user_id != user_id:
        raise DomainError(Failure.MISSING, "Conversation not found")
    return item


async def prepare_run(session, user, conversation_id, prompt, config, family_id=None):
    # One shared row is a lightweight global admission lock; no in-process semaphore.
    await session.scalars(select(RoleBudget).where(RoleBudget.role == "user").with_for_update())
    current = (
        await session.scalars(
            select(User)
            .where(User.id == user.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).one_or_none()
    if not eligible_account(current):
        raise DomainError(Failure.UNAUTHENTICATED, "Account access is no longer active")
    if family_id:
        await require_family(session, current, family_id, config)
    budget = await session.get(RoleBudget, current.role)
    if not budget.model_enabled or prompt.model != "default":
        raise DomainError(Failure.FORBIDDEN, "Model is not available for this role")
    conversation = await owned(session, conversation_id, user.id)
    if await session.scalar(
        select(Generation.id).where(
            Generation.user_id == user.id, Generation.request_key == prompt.request_key
        )
    ):
        raise DomainError(Failure.CONFLICT, "This request already exists; reload its conversation")
    await session.execute(
        update(Generation)
        .where(Generation.status == "streaming", Generation.expires_at <= now())
        .values(status="interrupted")
    )
    active = await session.scalar(
        select(func.count()).select_from(Generation).where(Generation.status == "streaming")
    )
    personal = await session.scalar(
        select(func.count())
        .select_from(Generation)
        .where(Generation.status == "streaming", Generation.user_id == user.id)
    )
    same_chat = await session.scalar(
        select(func.count())
        .select_from(Generation)
        .where(Generation.status == "streaming", Generation.conversation_id == conversation_id)
    )
    if (
        active >= config.global_concurrency
        or personal >= (current.max_concurrent or budget.max_concurrent)
        or same_chat
    ):
        raise DomainError(
            Failure.LIMITED, "Generation limit reached; wait or stop the active reply"
        )
    history = list(
        (
            await session.scalars(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at, Message.id)
            )
        ).all()
    )
    messages = [{"role": m.role, "content": m.content} for m in history if m.content]
    messages.append({"role": "user", "content": prompt.content})
    input_units = sum(len(m["content"].encode()) for m in messages)
    if input_units > 32000:
        raise DomainError(
            Failure.TOO_LARGE, "Conversation context is full; start a new conversation"
        )
    reservation = input_units + budget.max_output
    today = datetime.now(timezone.utc).date().isoformat()
    usage = await session.scalar(
        select(DailyUsage).where(DailyUsage.user_id == user.id, DailyUsage.day == today)
    )
    if not usage:
        usage = DailyUsage(user_id=user.id, day=today, requests=0, units=0)
        session.add(usage)
    if usage.requests >= (
        current.daily_requests or budget.daily_requests
    ) or usage.units + reservation > (current.daily_units or budget.daily_units):
        raise DomainError(Failure.LIMITED, "Daily budget reached")
    usage.requests += 1
    usage.units += reservation
    session.add(Message(conversation_id=conversation_id, role="user", content=prompt.content))
    reply = Message(conversation_id=conversation_id, role="assistant", content="")
    session.add(reply)
    await session.flush()
    run = Generation(
        user_id=user.id,
        conversation_id=conversation_id,
        request_key=prompt.request_key,
        message_id=reply.id,
        reserved_units=reservation,
        expires_at=now() + 150,
    )
    session.add(run)
    if conversation.title == "New conversation":
        conversation.title = prompt.content[:60]
    # Persist admission before external I/O: another worker must see the reserved
    # capacity, and a slow model must not hold these database locks for its stream.
    await session.commit()
    return run, messages, budget.max_output


async def generate(factory, provider, run, messages, max_output, tasks=None):
    content, status, tokens = "", GenerationState.FAILED, None
    ended = False
    task = asyncio.current_task()
    if tasks is not None:
        tasks.add(task)
    try:
        yield Started(run.id, run.message_id)
        async with asyncio.timeout(120):
            async for chunk in provider.stream(messages, max_output):
                async with factory() as session:
                    current = await session.get(Generation, run.id)
                    if current.cancel_requested:
                        status = GenerationState.CANCELLED
                        break
                if ended:
                    raise RuntimeError("Provider emitted output after completion")
                if isinstance(chunk, TextDelta):
                    content += chunk.text
                    if len(content.encode()) > max_output * 16:  # Adapter output safety ceiling.
                        raise RuntimeError("Provider output exceeded safety ceiling")
                    yield Delta(chunk.text)
                elif isinstance(chunk, TokenUsage):
                    tokens = chunk.tokens
                elif isinstance(chunk, StreamEnd):
                    status, ended = provider_outcome(chunk.status), True
                else:
                    raise RuntimeError("Provider emitted an invalid event")
            if not ended and status != GenerationState.CANCELLED:
                raise RuntimeError("Provider stream ended without completion")
    except (asyncio.CancelledError, GeneratorExit):
        status = GenerationState.CANCELLED
        raise
    except Exception:
        status = GenerationState.FAILED
        yield Error("Provider unavailable. Your conversation was saved.")
    finally:
        try:
            # Starlette cancels response tasks on disconnect. Shield durable cleanup.
            with anyio.CancelScope(shield=True):
                async with factory() as session:
                    await session.execute(
                        update(Message).where(Message.id == run.message_id).values(content=content)
                    )
                    await session.execute(
                        update(Generation)
                        .where(Generation.id == run.id)
                        .values(status=status, actual_tokens=tokens)
                    )
                    await session.commit()
        finally:
            if tasks is not None:
                tasks.discard(task)
    yield Completed(status, tokens)


async def issue_recovery(session, user, actor_id):
    value = secret_token()
    await session.execute(delete(Recovery).where(Recovery.user_id == user.id))
    session.add(Recovery(digest=digest(value), user_id=user.id, expires_at=now() + 1800))
    session.add(Audit(actor_id=actor_id, action="recovery.issued", target_id=user.id))
    await session.commit()
    return value


async def consume_link(session, value, purpose):
    token = await session.get(Recovery, digest(value))
    if not token or token.purpose != purpose:
        raise DomainError(Failure.INVALID, "Invalid or expired link")
    # Lock the user before token rows: different links for one owner cannot
    # deadlock while invalidating siblings, or both change the account.
    user = await session.get(User, token.user_id, with_for_update=True)
    await session.refresh(token)
    if token.used or token.expires_at <= now():
        raise DomainError(Failure.INVALID, "Invalid or expired link")
    await session.execute(
        update(Recovery)
        .where(Recovery.user_id == user.id, Recovery.purpose == purpose)
        .values(used=True)
    )
    return user
