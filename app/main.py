import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import database
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
    User,
    now,
)
from app.providers import make_provider
from app.schemas import BudgetEdit, Credentials, Login, Prompt, ResetPassword, Title, UserEdit
from app.security import DUMMY_HASH, decode_token, digest, hash_password, verify_password
from app.services import (
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

log = logging.getLogger("chat")


def create_app(config=None, provider=None):
    config = config or Settings()
    engine, factory = database(config.database_url)
    adapter = provider or make_provider(config)

    @asynccontextmanager
    async def lifespan(_):  # pragma: no cover - server lifecycle verified by container E2E
        yield
        await engine.dispose()

    app = FastAPI(
        title="373 Chat", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )
    app.state.engine, app.state.factory, app.state.config = engine, factory, config

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
        response = await call_next(request)
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
        user = User(
            email=str(body.email).lower(),
            password_hash=hash_password(body.password),
            approved=config.registration_policy == "open",
        )
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(409, "Account cannot be registered")
        return {
            "message": "Account created. Sign in."
            if user.approved
            else "Account created. An administrator must approve it."
        }

    @app.post("/api/auth/login")
    async def login(
        body: Login, response: Response, request: Request, db: AsyncSession = Depends(session)
    ):
        if request.headers.get("origin"):
            same_origin(request)
        await throttle(db, "login:" + request.client.host, 10)
        user = await db.scalar(select(User).where(User.email == str(body.email).lower()))
        valid = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
        if not valid or not user or not user.active or not user.approved:
            raise HTTPException(401, "Invalid credentials or account awaiting approval")
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

    @app.post("/api/auth/reset", status_code=204)
    async def reset(body: ResetPassword, request: Request, db: AsyncSession = Depends(session)):
        await throttle(db, "reset:" + request.client.host, 5)
        recovery = await db.get(Recovery, digest(body.token), with_for_update=True)
        if not recovery or recovery.used or recovery.expires_at <= now():
            raise HTTPException(400, "Invalid or expired recovery link")
        user = await db.get(User, recovery.user_id)
        user.password_hash = hash_password(body.password)
        recovery.used = True
        await revoke_all(db, user.id)
        db.add(Audit(actor_id=user.id, action="password.reset", target_id=user.id))
        await db.commit()

    @app.post("/api/auth/password", status_code=204)
    async def change_password(
        body: Credentials, user=Depends(current), db: AsyncSession = Depends(session)
    ):
        user.password_hash = hash_password(body.password)
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
    async def conversations(user=Depends(current), db: AsyncSession = Depends(session)):
        items = (
            await db.scalars(
                select(Conversation)
                .where(Conversation.user_id == user.id)
                .order_by(Conversation.created_at.desc())
                .limit(100)
            )
        ).all()
        return [{"id": c.id, "title": c.title} for c in items]

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
        messages = (
            await db.scalars(
                select(Message)
                .where(Message.conversation_id == cid)
                .order_by(Message.created_at, Message.id)
            )
        ).all()
        runs = (await db.scalars(select(Generation).where(Generation.conversation_id == cid))).all()
        return {
            "id": item.id,
            "title": item.title,
            "messages": [{"id": m.id, "role": m.role, "content": m.content} for m in messages],
            "runs": [{"id": r.id, "status": r.status, "tokens": r.actual_tokens} for r in runs],
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
    async def users(_=Depends(admin), db: AsyncSession = Depends(session)):
        return [
            user_view(u)
            for u in (
                await db.scalars(select(User).order_by(User.created_at.desc()).limit(200))
            ).all()
        ]

    @app.patch("/api/admin/users/{uid}")
    async def edit_user(
        uid: str, body: UserEdit, actor=Depends(admin), db: AsyncSession = Depends(session)
    ):
        if uid == actor.id:
            raise HTTPException(400, "Use another administrator to change your access")
        user = await db.get(User, uid, with_for_update=True)
        if not user:
            raise HTTPException(404, "User not found")
        for key, value in body.model_dump().items():
            setattr(user, key, value)
        await revoke_all(db, uid)
        db.add(Audit(actor_id=actor.id, action="user.updated", target_id=uid))
        await db.commit()
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
