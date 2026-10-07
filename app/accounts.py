"""Account-access use case: authority and its effect share one transaction."""

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.email import MailCapacityExceeded, enqueue, token_email
from app.errors import DomainError, Failure
from app.models import Audit, RoleBudget, User
from app.services import consume_link, revoke_all


async def edit_account(db, actor, target_id, changes, config):
    if target_id == actor.id:
        raise DomainError(Failure.INVALID, "Use another administrator to change your access")
    # Target-row locks alone cannot serialize reciprocal A→B / B→A edits.
    # One stable row serializes access edits; reloading the actor after acquiring
    # it prevents a request authenticated earlier from exercising revoked power.
    if db.bind.dialect.name == "sqlite":
        await db.execute(text("UPDATE role_budgets SET role=role WHERE role='admin'"))
    else:
        await db.scalars(select(RoleBudget).where(RoleBudget.role == "admin").with_for_update())
    await db.refresh(actor)
    if not (actor.role == "admin" and actor.active and actor.approved and actor.email_verified):
        raise DomainError(Failure.FORBIDDEN, "Administrator access is no longer active")
    user = await db.get(User, target_id, with_for_update=True)
    if not user:
        raise DomainError(Failure.MISSING, "User not found")
    newly_approved = changes.approved and not user.approved
    for key, value in changes.model_dump().items():
        setattr(user, key, value)
    # The eligible actor cannot edit their own access. After serialization and
    # revalidation, that actor remains an eligible administrator after this edit.
    await revoke_all(db, target_id)
    if newly_approved:
        await enqueue(
            db,
            config,
            user.email,
            "Your Firehose360 account is approved",
            "You can now sign in at " + config.base_url + "."
            if user.email_verified
            else "Your account is approved. Verify your email using the registration link before signing in. "
            "If it expired, request another verification link at " + config.base_url + ".",
        )
    db.add(Audit(actor_id=actor.id, action="user.updated", target_id=target_id))
    await db.commit()
    return user


PUBLIC_REGISTRATION = {
    "message": "If registration is available, check your inbox for the next steps."
}


async def register_account(db, email, hashed, config):
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
        raise DomainError(Failure.CONFLICT, "Account cannot be registered")
    except MailCapacityExceeded:
        # Account, link and outbox either commit together or leave no new account.
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


async def request_link(db, email, purpose, config):
    user = await db.scalar(select(User).where(User.email == email))
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
    return {"message": "If the account is eligible, an email will arrive shortly. Check spam too."}


async def verify_address(db, token):
    user = await consume_link(db, token, "verify")
    user.email_verified = True
    db.add(Audit(actor_id=user.id, action="email.verified", target_id=user.id))
    await db.commit()
    return {
        "message": "Email verified. You can sign in."
        if user.approved
        else "Email verified. Sign in once your administrator approves the account."
    }


async def reset_account_password(db, token, hashed):
    user = await consume_link(db, token, "reset")
    await set_password(db, user, hashed, "password.reset")


async def set_password(db, user, hashed, action):
    user.password_hash = hashed
    await revoke_all(db, user.id)
    db.add(Audit(actor_id=user.id, action=action, target_id=user.id))
    await db.commit()
