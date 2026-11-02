from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def make_engine(url):
    kwargs = {"pool_pre_ping": True}
    if url.startswith("mysql"):
        # Each read sees committed duplicate inserts after a uniqueness conflict.
        # Atomic conditional updates and unique constraints enforce write invariants.
        kwargs["isolation_level"] = "READ COMMITTED"
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")

    return engine


@contextmanager
def transaction(engine):
    with Session(engine) as session, session.begin():
        yield session
