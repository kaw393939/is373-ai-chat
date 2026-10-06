"""One-off operational commands use the same models and environment as the app."""

import argparse
import asyncio
import getpass
import os

from sqlalchemy import delete, select

from app.config import Settings
from app.db import database
from app.models import EmailOutbox, Family, Recovery, RoleBudget, Throttle, User, now
from app.security import hash_password


async def execute(args):  # pragma: no cover - operational adapter; verified via container install
    engine, factory = database(Settings().database_url)
    async with factory() as db:
        for role in ["user", "admin"]:
            if not await db.get(RoleBudget, role):
                db.add(RoleBudget(role=role))
        if args.command == "admin":
            password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Admin password: ")
            if len(password) < 16:
                raise SystemExit("Admin password must be at least 16 characters")
            if not await db.scalar(select(User).where(User.email == args.email.lower())):
                db.add(
                    User(
                        email=args.email.lower(),
                        password_hash=hash_password(password),
                        role="admin",
                        approved=True,
                    )
                )
        if args.command == "prune":
            await db.execute(
                delete(EmailOutbox).where(
                    EmailOutbox.created_at < now() - 32 * 86400, EmailOutbox.status != "pending"
                )
            )
            await db.execute(delete(Throttle).where(Throttle.expires_at < now()))
            await db.execute(delete(Recovery).where(Recovery.expires_at < now()))
            await db.execute(delete(Family).where(Family.expires_at < now()))
        await db.commit()
    await engine.dispose()


def main():  # pragma: no cover - CLI parser, not application behavior
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["seed", "admin", "prune"])
    parser.add_argument("--email", default="admin@example.org")
    asyncio.run(execute(parser.parse_args()))


if __name__ == "__main__":
    main()
