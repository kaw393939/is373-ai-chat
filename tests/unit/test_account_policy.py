"""SQLite fallback still reloads actor authority before changing another user."""

import pytest

from app.accounts import edit_account
from app.config import Settings
from app.db import database
from app.errors import DomainError, Failure
from app.models import Base, RoleBudget, User
from app.schemas import UserEdit


async def test_sqlite_access_lock_rejects_stale_actor(tmp_path):
    engine, factory = database(f"sqlite+aiosqlite:///{tmp_path}/account-policy.db")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as db:
        actor = User(
            email="first@example.org", password_hash="synthetic", role="admin", approved=True
        )
        target = User(
            email="second@example.org", password_hash="synthetic", role="admin", approved=True
        )
        db.add_all([RoleBudget(role="admin"), actor, target])
        await db.commit()
        async with factory() as peer:
            stale = await peer.get(User, actor.id)
            stale.approved = False
            await peer.commit()
        assert actor.approved  # Deliberately cached pre-change authority.
        with pytest.raises(DomainError) as rejected:
            await edit_account(
                db,
                actor,
                target.id,
                UserEdit(role="user", active=False, approved=False),
                Settings(),
            )
        assert rejected.value.kind == Failure.FORBIDDEN
        await db.refresh(target)
        assert target.role == "admin" and target.active and target.approved
    await engine.dispose()
