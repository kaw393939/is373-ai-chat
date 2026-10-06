"""Share a pool/session factory, never one mutable session across async tasks.

Use cases own transaction boundaries. See book/03-data.md for why a database
transaction should not remain open while an external model streams a reply.
"""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def database(url):
    options = {"pool_pre_ping": True}
    if url.startswith("postgresql"):
        # Bound connections per process; replicas multiply this pool budget.
        options.update(pool_size=5, max_overflow=0)
    engine = create_async_engine(url, **options)
    if url.startswith("sqlite"):

        @event.listens_for(engine.sync_engine, "connect")
        def foreign_keys(connection, _):
            # SQLite needs explicit enforcement; otherwise local tests can
            # accept relationships PostgreSQL would reject.
            connection.execute("PRAGMA foreign_keys=ON")

    # Committed objects remain readable without implicit async reloads; callers
    # must explicitly refresh values when they need current database state.
    return engine, async_sessionmaker(engine, expire_on_commit=False)
