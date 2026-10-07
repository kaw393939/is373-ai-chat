import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from typing import Literal
from urllib.parse import urlparse
from uuid import uuid4

import anyio
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.accounts import edit_account
from app.config import Settings
from app.db import database
from app.email import MailCapacityExceeded, drain, make_mailer, token_email
from app.exports import owned_export
from app.middleware import BodyLimit
from app.models import (
    Audit,
    Conversation,
    DailyUsage,
    EmailOutbox,
    Family,
    Generation,
    Message,
    Refresh,
    RoleBudget,
    User,
    now,
)
from app.pagination import page_rows
from app.providers import make_provider
from app.schemas import (
    BudgetEdit,
    ChangePassword,
    Credentials,
    EmailAddress,
    Login,
    Prompt,
    ResetPassword,
    Title,
    UserEdit,
    VerifyEmail,
)
from app.security import DUMMY_HASH, decode_token, digest, hash_password, verify_password
from app.services import (
    consume_link,
    generate,
    issue_recovery,
    new_session,
    owned,
    prepare_run,
    revoke_all,
    rotate,
    throttle,
    user_view,
)

log = logging.getLogger("uvicorn.error")
PUBLIC_REGISTRATION = {
    "message": "If registration is available, check your inbox for the next steps."
}


def create_app(config=None, provider=None):
    config = config or Settings()
    engine, factory = database(config.database_url)
    adapter = provider or make_provider(config)
    mailer = make_mailer(config)
    password_limiter = anyio.CapacityLimiter(2)

    async def password_hash(value):
        return await anyio.to_thread.run_sync(hash_password, value, limiter=password_limiter)

    async def password_valid(value, hashed):
        return await anyio.to_thread.run_sync(
            verify_password, value, hashed, limiter=password_limiter
        )

    async def mail_loop():  # pragma: no cover - lifecycle loop; delivery behavior tested directly
        while True:
            try:
                await drain(factory, config, mailer)
            except Exception:
                log.error("Email worker unavailable")
            await asyncio.sleep(5)

    @asynccontextmanager
    async def lifespan(_):  # pragma: no cover - server lifecycle verified by container E2E
        task = asyncio.create_task(mail_loop()) if config.email_provider != "disabled" else None
        try:
            yield
        finally:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await engine.dispose()

    app = FastAPI(
        title="373 Chat", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )
    app.state.engine, app.state.factory, app.state.config = engine, factory, config
    app.state.mailer = mailer
    app.add_middleware(BodyLimit)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[urlparse(config.base_url).hostname, "localhost", "127.0.0.1"],
    )

    @app.exception_handler(RequestValidationError)
    async def invalid_inputs(_, exc):
        # Pydantic's default error contains submitted inputs, including passwords.
        return JSONResponse({"detail": "Invalid request inputs"}, status_code=422)

    async def session():
        async with factory() as db:
            yield db

    def same_origin(request):
        origin = request.headers.get("origin")
        if origin != config.base_url.rstrip("/"):
            raise HTTPException(403, "Same-origin request required")

    async def current(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
        db: AsyncSession = Depends(session),
    ):
        if not credentials:
            raise HTTPException(401, "Sign in required")
        claims = decode_token(credentials.credentials, config)
        family = await db.get(Family, claims["sid"])
        user = await db.get(User, claims["sub"])
        if (
            not family
            or family.user_id != claims["sub"]
            or family.revoked
            or family.expires_at <= now()
            or not user
            or not user.active
            or not user.approved
            or not user.email_verified
        ):
            raise HTTPException(401, "Session is no longer active")
        request.state.family_id = family.id
        return user

    async def admin(user=Depends(current)):
        if user.role != "admin":
            raise HTTPException(403, "Administrator access required")
        return user

    def set_refresh(response, value):
        response.set_cookie(
            "refresh",
            value,
            httponly=True,
            secure=config.secure_cookie,
            samesite="strict",
            path="/api/auth",
            max_age=config.refresh_days * 86400,
        )

    @app.middleware("http")
    async def security_headers(request, call_next):
        started = perf_counter()
        request_id = uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        log.info(
            json.dumps(
                {
                    "event": "response_started",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "response_start_ms": round((perf_counter() - started) * 1000, 2),
                }
            )
        )
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "same-origin",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
            }
        )
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        if config.secure_cookie:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.get("/api/health")
    async def health(db: AsyncSession = Depends(session)):
        await db.execute(text("SELECT 1"))
        revision = (await db.execute(text("SELECT version_num FROM alembic_version"))).scalar()
        return {
            "status": "ok",
            "commit": config.commit_sha,
            "schema": revision,
            "provider": config.provider,
        }

    @app.post("/api/auth/register", status_code=201)
    async def register(body: Credentials, request: Request, db: AsyncSession = Depends(session)):
        await throttle(db, "register:" + request.client.host, 5)
        email = str(body.email).lower()
        hashed = await password_hash(body.password)
        if config.email_provider != "disabled" and await db.scalar(
            select(User).where(User.email == email)
        ):
            return PUBLIC_REGISTRATION
        user = User(
            email=email,
            password_hash=hashed,
            approved=config.registration_policy == "open",
            email_verified=config.email_provider == "disabled",
        )
        db.add(user)
        try:
            await db.flush()
            if config.email_provider != "disabled":
                await token_email(db, config, user, "verify")
            await db.commit()
        except IntegrityError:
            await db.rollback()
            if config.email_provider != "disabled":
                return PUBLIC_REGISTRATION
            raise HTTPException(409, "Account cannot be registered")
        except MailCapacityExceeded:
            # The account, link and outbox are one unit; no undeliverable account
            # survives. Anonymous callers see the same receipt as duplicates.
            await db.rollback()
            return PUBLIC_REGISTRATION
        return (
            PUBLIC_REGISTRATION
            if not user.email_verified
            else {
                "message": "Account created. Sign in."
                if user.approved
                else "Account created. An administrator must approve it."
            }
        )

    @app.post("/api/auth/login")
    async def login(
        body: Login, response: Response, request: Request, db: AsyncSession = Depends(session)
    ):
        if request.headers.get("origin"):
            same_origin(request)
        await throttle(db, "login:" + request.client.host, 10)
        await throttle(db, "login-account:" + str(body.email).lower(), 10)
        user = await db.scalar(select(User).where(User.email == str(body.email).lower()))
        valid = await password_valid(body.password, user.password_hash if user else DUMMY_HASH)
        if not valid or not user or not user.active or not user.approved or not user.email_verified:
            raise HTTPException(
                401, "Invalid credentials or account awaiting verification/approval"
            )
        access, refresh = await new_session(db, user, config)
        set_refresh(response, refresh)
        return {"access_token": access, "user": user_view(user)}

    @app.post("/api/auth/refresh")
    async def refresh(request: Request, response: Response, db: AsyncSession = Depends(session)):
        same_origin(request)
        access, fresh = await rotate(db, request.cookies.get("refresh", ""), config)
        set_refresh(response, fresh)
        return {"access_token": access}

    @app.post("/api/auth/logout", status_code=204)
    async def logout(request: Request, response: Response, db: AsyncSession = Depends(session)):
        same_origin(request)
        token = await db.get(Refresh, digest(request.cookies.get("refresh", "")))
        if token:
            family = await db.get(Family, token.family_id)
            family.revoked = True
            await db.commit()
        response.delete_cookie(
            "refresh",
            path="/api/auth",
            secure=config.secure_cookie,
            httponly=True,
            samesite="strict",
        )

    @app.get("/api/auth/me")
    async def me(user=Depends(current)):
        return user_view(user)

    @app.get("/api/account/export")
    async def export_data(
        section: Literal["conversations", "messages", "runs"] = "conversations",
        limit: int = Query(100, ge=1, le=100),
        cursor: str | None = Query(None, max_length=512),
        user=Depends(current),
        db: AsyncSession = Depends(session),
    ):
        await throttle(db, "export:" + user.id, 10)
        data = await owned_export(db, user, section, limit, cursor, config.jwt_secret)
        return {"account": user_view(user), **data}

    @app.get("/api/auth/options")
    async def auth_options():
        return {
            "email_enabled": config.email_provider != "disabled",
            "approval_required": config.registration_policy == "approval",
        }

    @app.post("/api/auth/email")
    async def request_email(
        body: EmailAddress,
        request: Request,
        purpose: str = "reset",
        db: AsyncSession = Depends(session),
    ):
        if config.email_provider == "disabled":
            raise HTTPException(503, "Contact your administrator for a recovery link")
        if purpose not in {"verify", "reset"}:
            raise HTTPException(400, "Unsupported email request")
        await throttle(db, "email-ip:" + request.client.host, 5)
        await throttle(db, "email-account:" + str(body.email).lower(), 1)
        user = await db.scalar(select(User).where(User.email == str(body.email).lower()))
        if (
            user
            and user.active
            and (
                (purpose == "verify" and not user.email_verified)
                or (purpose == "reset" and user.approved and user.email_verified)
            )
        ):
            try:
                await token_email(db, config, user, purpose)
                await db.commit()
            except MailCapacityExceeded:
                await db.rollback()
        return {
            "message": "If the account is eligible, an email will arrive shortly. Check spam too."
        }

    @app.post("/api/auth/verify")
    async def verify_email(
        body: VerifyEmail, request: Request, db: AsyncSession = Depends(session)
    ):
        await throttle(db, "verify:" + request.client.host, 5)
        user = await consume_link(db, body.token, "verify")
        user.email_verified = True
        db.add(Audit(actor_id=user.id, action="email.verified", target_id=user.id))
        await db.commit()
        return {
            "message": "Email verified. You can sign in."
            if user.approved
            else "Email verified. Sign in once your administrator approves the account."
        }

    @app.post("/api/auth/reset", status_code=204)
    async def reset(body: ResetPassword, request: Request, db: AsyncSession = Depends(session)):
        await throttle(db, "reset:" + request.client.host, 5)
        user = await consume_link(db, body.token, "reset")
        user.password_hash = await password_hash(body.password)
        await revoke_all(db, user.id)
        db.add(Audit(actor_id=user.id, action="password.reset", target_id=user.id))
        await db.commit()

    @app.post("/api/auth/password", status_code=204)
    async def change_password(
        body: ChangePassword, user=Depends(current), db: AsyncSession = Depends(session)
    ):
        await throttle(db, "password:" + user.id, 5)
        if not await password_valid(body.current_password, user.password_hash):
            raise HTTPException(400, "Current password is incorrect")
        user.password_hash = await password_hash(body.password)
        db.add(user)
        await revoke_all(db, user.id)
        db.add(Audit(actor_id=user.id, action="password.changed", target_id=user.id))
        await db.commit()

    @app.get("/api/models")
    async def models(user=Depends(current), db: AsyncSession = Depends(session)):
        budget = await db.get(RoleBudget, user.role)
        return [
            {
                "id": "default",
                "name": "Workshop mock" if config.provider == "mock" else config.provider_model,
                "provider": config.provider,
                "enabled": budget.model_enabled,
            }
        ]

    @app.get("/api/conversations")
    async def conversations(
        page: bool = False,
        limit: int = Query(50, ge=1, le=100),
        cursor: str | None = Query(None, max_length=512),
        q: str = Query("", max_length=100),
        user=Depends(current),
        db: AsyncSession = Depends(session),
    ):
        statement = select(Conversation).where(Conversation.user_id == user.id)
        if q:
            statement = statement.where(Conversation.title.icontains(q, autoescape=True))
        items, next_cursor = await page_rows(
            db,
            Conversation,
            statement,
            limit if page else 100,
            cursor,
            f"conversations:{user.id}:{q}",
            config.jwt_secret,
        )
        views = [{"id": c.id, "title": c.title} for c in items]
        return {"items": views, "next_cursor": next_cursor} if page else views

    @app.post("/api/conversations", status_code=201)
    async def create_conversation(user=Depends(current), db: AsyncSession = Depends(session)):
        await throttle(db, "conversation:" + user.id, 20)
        item = Conversation(user_id=user.id)
        db.add(item)
        await db.commit()
        return {"id": item.id, "title": item.title}

    @app.get("/api/conversations/{cid}")
    async def conversation(cid: str, user=Depends(current), db: AsyncSession = Depends(session)):
        item = await owned(db, cid, user.id)
        messages, messages_cursor = await page_rows(
            db,
            Message,
            select(Message).where(Message.conversation_id == cid),
            50,
            None,
            f"messages:{user.id}:{cid}",
            config.jwt_secret,
        )
        runs, runs_cursor = await page_rows(
            db,
            Generation,
            select(Generation).where(Generation.conversation_id == cid),
            50,
            None,
            f"runs:{user.id}:{cid}",
            config.jwt_secret,
        )
        return {
            "id": item.id,
            "title": item.title,
            "messages": [
                {"id": m.id, "role": m.role, "content": m.content} for m in reversed(messages)
            ],
            "runs": [
                {"id": r.id, "status": r.status, "tokens": r.actual_tokens} for r in reversed(runs)
            ],
            "messages_cursor": messages_cursor,
            "runs_cursor": runs_cursor,
        }

    @app.get("/api/conversations/{cid}/messages")
    async def message_page(
        cid: str,
        limit: int = Query(50, ge=1, le=100),
        cursor: str | None = Query(None, max_length=512),
        user=Depends(current),
        db: AsyncSession = Depends(session),
    ):
        await owned(db, cid, user.id)
        items, next_cursor = await page_rows(
            db,
            Message,
            select(Message).where(Message.conversation_id == cid),
            limit,
            cursor,
            f"messages:{user.id}:{cid}",
            config.jwt_secret,
        )
        return {
            "items": [{"id": m.id, "role": m.role, "content": m.content} for m in reversed(items)],
            "next_cursor": next_cursor,
        }

    @app.get("/api/conversations/{cid}/runs")
    async def run_page(
        cid: str,
        limit: int = Query(50, ge=1, le=100),
        cursor: str | None = Query(None, max_length=512),
        user=Depends(current),
        db: AsyncSession = Depends(session),
    ):
        await owned(db, cid, user.id)
        items, next_cursor = await page_rows(
            db,
            Generation,
            select(Generation).where(Generation.conversation_id == cid),
            limit,
            cursor,
            f"runs:{user.id}:{cid}",
            config.jwt_secret,
        )
        return {
            "items": [
                {"id": r.id, "status": r.status, "tokens": r.actual_tokens} for r in reversed(items)
            ],
            "next_cursor": next_cursor,
        }

    @app.patch("/api/conversations/{cid}")
    async def rename(
        cid: str, body: Title, user=Depends(current), db: AsyncSession = Depends(session)
    ):
        item = await owned(db, cid, user.id)
        item.title = body.title
        await db.commit()
        return {"id": cid, "title": item.title}

    @app.delete("/api/conversations/{cid}", status_code=204)
    async def remove(cid: str, user=Depends(current), db: AsyncSession = Depends(session)):
        await owned(db, cid, user.id)
        if await db.scalar(
            select(Generation.id).where(
                Generation.conversation_id == cid,
                Generation.status == "streaming",
                Generation.expires_at > now(),
            )
        ):
            raise HTTPException(409, "Stop the active generation first")
        await db.execute(delete(Conversation).where(Conversation.id == cid))
        await db.commit()

    @app.post("/api/conversations/{cid}/stream")
    async def stream(
        cid: str, body: Prompt, user=Depends(current), db: AsyncSession = Depends(session)
    ):
        run, history, max_output = await prepare_run(db, user, cid, body, config)
        return StreamingResponse(
            generate(factory, adapter, run, history, max_output),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    @app.post("/api/generations/{rid}/cancel", status_code=204)
    async def cancel(rid: str, user=Depends(current), db: AsyncSession = Depends(session)):
        run = await db.get(Generation, rid)
        if not run or run.user_id != user.id:
            raise HTTPException(404, "Generation not found")
        run.cancel_requested = True
        await db.commit()

    @app.get("/api/admin/users")
    async def users(
        page: bool = False,
        limit: int = Query(50, ge=1, le=100),
        cursor: str | None = Query(None, max_length=512),
        q: str = Query("", max_length=100),
        actor=Depends(admin),
        db: AsyncSession = Depends(session),
    ):
        statement = select(User)
        if q:
            statement = statement.where(User.email.icontains(q, autoescape=True))
        items, next_cursor = await page_rows(
            db,
            User,
            statement,
            limit if page else 200,
            cursor,
            f"users:{actor.id}:{q}",
            config.jwt_secret,
        )
        views = [user_view(u) for u in items]
        return {"items": views, "next_cursor": next_cursor} if page else views

    @app.patch("/api/admin/users/{uid}")
    async def edit_user(
        uid: str, body: UserEdit, actor=Depends(admin), db: AsyncSession = Depends(session)
    ):
        user = await edit_account(db, actor, uid, body, config)
        return user_view(user)

    @app.post("/api/admin/users/{uid}/recovery")
    async def recovery(uid: str, actor=Depends(admin), db: AsyncSession = Depends(session)):
        user = await db.get(User, uid)
        if not user:
            raise HTTPException(404, "User not found")
        token = await issue_recovery(db, user, actor.id)
        return {"url": config.base_url + "/#reset=" + token, "expires_minutes": 30}

    @app.post("/api/admin/users/{uid}/revoke", status_code=204)
    async def revoke(uid: str, actor=Depends(admin), db: AsyncSession = Depends(session)):
        await revoke_all(db, uid)
        db.add(Audit(actor_id=actor.id, action="sessions.revoked", target_id=uid))
        await db.commit()

    @app.get("/api/admin/budgets")
    async def budgets(_=Depends(admin), db: AsyncSession = Depends(session)):
        return [
            {"role": b.role, **{k: getattr(b, k) for k in BudgetEdit.model_fields}}
            for b in (await db.scalars(select(RoleBudget))).all()
        ]

    @app.put("/api/admin/budgets/{role}")
    async def edit_budget(
        role: str, body: BudgetEdit, actor=Depends(admin), db: AsyncSession = Depends(session)
    ):
        budget = await db.get(RoleBudget, role)
        if not budget:
            raise HTTPException(404, "Role not found")
        for key, value in body.model_dump().items():
            setattr(budget, key, value)
        db.add(Audit(actor_id=actor.id, action="budget.updated", target_id=role))
        await db.commit()
        return {"message": "Budget saved"}

    @app.get("/api/admin/overview")
    async def overview(_=Depends(admin), db: AsyncSession = Depends(session)):
        try:
            metrics = json.loads(Path(config.metrics_path).read_text())
        except (OSError, ValueError):
            metrics = {"status": "collector unavailable", "samples": []}
        totals = {
            "users": await db.scalar(select(func.count()).select_from(User)),
            "active_streams": await db.scalar(
                select(func.count())
                .select_from(Generation)
                .where(Generation.status == "streaming", Generation.expires_at > now())
            ),
            "failed_runs": await db.scalar(
                select(func.count()).select_from(Generation).where(Generation.status == "failed")
            ),
            "requests": await db.scalar(select(func.coalesce(func.sum(DailyUsage.requests), 0))),
            "reserved_units": await db.scalar(select(func.coalesce(func.sum(DailyUsage.units), 0))),
            "email_pending": await db.scalar(
                select(func.count()).select_from(EmailOutbox).where(EmailOutbox.status == "pending")
            ),
            "email_failed": await db.scalar(
                select(func.count()).select_from(EmailOutbox).where(EmailOutbox.status == "failed")
            ),
            "email_sent": await db.scalar(
                select(func.count()).select_from(EmailOutbox).where(EmailOutbox.status == "sent")
            ),
        }
        audits = (await db.scalars(select(Audit).order_by(Audit.created_at.desc()).limit(20))).all()
        return {
            "totals": totals,
            "host": metrics,
            "audit": [
                {"action": a.action, "target": a.target_id, "at": a.created_at} for a in audits
            ],
        }

    if config.assets.is_dir():
        app.mount("/assets", StaticFiles(directory=config.assets / "assets"), name="assets")

    @app.get("/")
    async def index():
        if not (config.assets / "index.html").exists():
            raise HTTPException(503, "Build the frontend with npm run build")
        return FileResponse(config.assets / "index.html")

    return app
