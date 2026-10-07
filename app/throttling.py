"""Independent attempt accounting: rejection never commits a caller's work."""

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.errors import DomainError, Failure
from app.models import Throttle, now
from app.security import digest


async def throttle(factory, identity, limit=10):
    async with factory() as session:
        bucket = int(now() // 60)
        key = digest(f"{identity}:{bucket}")
        insert = pg_insert if session.bind.dialect.name == "postgresql" else sqlite_insert
        statement = insert(Throttle).values(key=key, count=1, expires_at=now() + 120)
        statement = statement.on_conflict_do_update(
            index_elements=[Throttle.key], set_={"count": Throttle.count + 1}
        ).returning(Throttle.count)
        count = (await session.execute(statement)).scalar_one()
        await session.commit()
    if count > limit:
        raise DomainError(Failure.LIMITED, "Too many attempts; try again in a minute")
