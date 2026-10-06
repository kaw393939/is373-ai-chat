from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def database(url):
    options = {"pool_pre_ping": True}
    if url.startswith("postgresql"):
        options.update(pool_size=5, max_overflow=0)
    engine = create_async_engine(url, **options)
    if url.startswith("sqlite"):

        @event.listens_for(engine.sync_engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    return engine, async_sessionmaker(engine, expire_on_commit=False)
