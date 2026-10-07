import pytest
from sqlalchemy import func, select

from app.errors import DomainError, Failure
from app.models import Audit, EmailOutbox, Family, Throttle, User, now
from app.throttling import throttle
from tests.conftest import login, signup
from tests.integration.test_email import enable


async def test_attempt_accounting_cannot_commit_unrelated_pending_work(application):
    async with application.state.factory() as db:
        user = await db.scalar(select(User))
        original = user.email
        user.email = "pending-uncommitted@example.org"
        await throttle(application.state.factory, "independent", 1)
        with pytest.raises(DomainError) as rejected:
            await throttle(application.state.factory, "independent", 1)
        assert rejected.value.kind == Failure.LIMITED
        await db.rollback()
    async with application.state.factory() as db:
        assert await db.scalar(select(User.email)) == original
        counter = await db.scalar(select(Throttle))
        assert counter.count == 2


async def test_account_approval_outbox_and_revocation_roll_back_together(client, application):
    learner = await signup(client)
    async with application.state.factory() as db:
        user = await db.get(User, learner["id"])
        user.approved = False
        for _ in range(80):
            db.add(EmailOutbox(payload="synthetic", expires_at=now() + 300))
        await db.commit()
    await login(client)
    enable(application)
    response = await client.patch(
        f"/api/admin/users/{learner['id']}", json={"role": "user", "active": True, "approved": True}
    )
    assert response.status_code == 503
    async with application.state.factory() as db:
        user = await db.get(User, learner["id"])
        assert not user.approved
        assert not await db.scalar(
            select(func.count()).select_from(Audit).where(Audit.action == "user.updated")
        )
        assert not (await db.scalar(select(Family).where(Family.user_id == learner["id"]))).revoked


async def test_admission_revalidates_locked_account_and_session(application):
    from app.models import Conversation
    from app.schemas import Prompt
    from app.services import prepare_run

    async with application.state.factory() as db:
        user = await db.scalar(select(User))
        conversation = Conversation(user_id=user.id)
        db.add(conversation)
        await db.commit()
        cid = conversation.id
        async with application.state.factory() as peer:
            current = await peer.get(User, user.id)
            current.active = False
            await peer.commit()
        with pytest.raises(DomainError) as rejected:
            await prepare_run(
                db,
                user,
                cid,
                Prompt(content="synthetic", request_key="stale-access-fixture"),
                application.state.config,
            )
        assert rejected.value.kind == Failure.UNAUTHENTICATED
        await db.rollback()
        await db.refresh(user)
        user.active = True
        await db.commit()
        with pytest.raises(DomainError) as rejected:
            await prepare_run(
                db,
                user,
                cid,
                Prompt(content="synthetic", request_key="missing-session-fixture"),
                application.state.config,
                "missing-family",
            )
        assert rejected.value.kind == Failure.UNAUTHENTICATED
