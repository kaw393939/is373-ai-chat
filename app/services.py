import asyncio
import json
from datetime import datetime, timezone

import anyio
from fastapi import HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.models import (
    Audit,
    Conversation,
    DailyUsage,
    Family,
    Generation,
    Message,
    Recovery,
    Refresh,
    RoleBudget,
    Throttle,
    User,
    now,
)
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


async def throttle(session, identity, limit=10):
    bucket = int(now() // 60)
    key = digest(f"{identity}:{bucket}")
    insert = pg_insert if session.bind.dialect.name == "postgresql" else sqlite_insert
    statement = insert(Throttle).values(key=key, count=1, expires_at=now() + 120)
    statement = statement.on_conflict_do_update(
        index_elements=[Throttle.key], set_={"count": Throttle.count + 1}
    ).returning(Throttle.count)
    count = (await session.execute(statement)).scalar_one()
    await session.commit()  # Rejected attempts still count.
    if count > limit:
        raise HTTPException(429, "Too many attempts; try again in a minute")


async def new_session(session, user, config):
    family = Family(user_id=user.id, expires_at=now() + config.refresh_days * 86400)
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
        raise HTTPException(401, "Invalid refresh session")
    family = (
        await session.scalars(select(Family).where(Family.id == token.family_id).with_for_update())
    ).one()
    await session.refresh(token)
    if token.used:
        family.revoked = True
        await session.commit()
        raise HTTPException(401, "Refresh reuse detected; sign in again")
    user = await session.get(User, family.user_id)
    if (
        family.revoked
        or family.expires_at <= now()
        or not user.active
        or not user.approved
        or not user.email_verified
    ):
        raise HTTPException(401, "Session revoked or expired")
    token.used = True
    fresh = secret_token()
    session.add(Refresh(digest=digest(fresh), family_id=family.id))
    await session.commit()
    return access_token(user.id, family.id, config), fresh


async def revoke_all(session, user_id):
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
        raise HTTPException(404, "Conversation not found")
    return item


async def prepare_run(session, user, conversation_id, prompt, config):
    # One shared row is a lightweight global admission lock; no in-process semaphore.
    await session.scalars(select(RoleBudget).where(RoleBudget.role == "user").with_for_update())
    current = (
        await session.scalars(select(User).where(User.id == user.id).with_for_update())
    ).one()
    budget = await session.get(RoleBudget, current.role)
    if not budget.model_enabled or prompt.model != "default":
        raise HTTPException(403, "Model is not available for this role")
    conversation = await owned(session, conversation_id, user.id)
    if await session.scalar(
        select(Generation.id).where(
            Generation.user_id == user.id, Generation.request_key == prompt.request_key
        )
    ):
        raise HTTPException(409, "This request already exists; reload its conversation")
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
        raise HTTPException(429, "Generation limit reached; wait or stop the active reply")
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
        raise HTTPException(413, "Conversation context is full; start a new conversation")
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
        raise HTTPException(429, "Daily budget reached")
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


def event(kind, data):
    return f"event: {kind}\ndata: {json.dumps(data)}\n\n"


async def generate(factory, provider, run, messages, max_output):
    content, status, tokens = "", "failed", None
    ended = False
    yield event("started", {"run_id": run.id, "message_id": run.message_id})
    try:
        async with asyncio.timeout(120):
            async for chunk in provider.stream(messages, max_output):
                async with factory() as session:
                    current = await session.get(Generation, run.id)
                    if current.cancel_requested:
                        status = "cancelled"
                        break
                if ended:
                    raise RuntimeError("Provider emitted output after completion")
                if isinstance(chunk, TextDelta):
                    content += chunk.text
                    if len(content.encode()) > max_output * 16:  # Adapter output safety ceiling.
                        raise RuntimeError("Provider output exceeded safety ceiling")
                    yield event("delta", {"text": chunk.text})
                elif isinstance(chunk, TokenUsage):
                    tokens = chunk.tokens
                elif isinstance(chunk, StreamEnd):
                    status, ended = chunk.status, True
                else:
                    raise RuntimeError("Provider emitted an invalid event")
            if not ended and status != "cancelled":
                raise RuntimeError("Provider stream ended without completion")
    except asyncio.CancelledError:  # pragma: no cover - ASGI disconnect exercised in browser tests
        status = "cancelled"
        raise
    except Exception:
        status = "failed"
        yield event("error", {"message": "Provider unavailable. Your conversation was saved."})
    finally:
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
    yield event("completed", {"status": status, "tokens": tokens})


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
        raise HTTPException(400, "Invalid or expired link")
    # Lock the user before token rows: different links for one owner cannot
    # deadlock while invalidating siblings, or both change the account.
    user = await session.get(User, token.user_id, with_for_update=True)
    await session.refresh(token)
    if token.used or token.expires_at <= now():
        raise HTTPException(400, "Invalid or expired link")
    await session.execute(
        update(Recovery)
        .where(Recovery.user_id == user.id, Recovery.purpose == purpose)
        .values(used=True)
    )
    return user
