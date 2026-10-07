"""Account-access use case: authority and its effect share one transaction."""

from fastapi import HTTPException
from sqlalchemy import select, text

from app.email import enqueue
from app.models import Audit, RoleBudget, User
from app.services import revoke_all


async def edit_account(db, actor, target_id, changes, config):
    if target_id == actor.id:
        raise HTTPException(400, "Use another administrator to change your access")
    # Target-row locks alone cannot serialize reciprocal A→B / B→A edits.
    # One stable row serializes access edits; reloading the actor after acquiring
    # it prevents a request authenticated earlier from exercising revoked power.
    if db.bind.dialect.name == "sqlite":
        await db.execute(text("UPDATE role_budgets SET role=role WHERE role='admin'"))
    else:
        await db.scalars(select(RoleBudget).where(RoleBudget.role == "admin").with_for_update())
    await db.refresh(actor)
    if not (actor.role == "admin" and actor.active and actor.approved and actor.email_verified):
        raise HTTPException(403, "Administrator access is no longer active")
    user = await db.get(User, target_id, with_for_update=True)
    if not user:
        raise HTTPException(404, "User not found")
    newly_approved = changes.approved and not user.approved
    for key, value in changes.model_dump().items():
        setattr(user, key, value)
    # The eligible actor cannot edit their own access. After serialization and
    # revalidation, that actor remains an eligible administrator after this edit.
    await revoke_all(db, target_id)
    if newly_approved and user.email_verified:
        await enqueue(
            db,
            config,
            user.email,
            "Your Firehose360 account is approved",
            "You can now sign in at " + config.base_url + ".",
        )
    db.add(Audit(actor_id=actor.id, action="user.updated", target_id=target_id))
    await db.commit()
    return user
