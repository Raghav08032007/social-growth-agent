import os

import pytest

from growth import create_app
from growth.config import Settings
from growth.db import transaction
from growth.models import Base, Membership, User, Workspace
from growth.security import issue_session


@pytest.fixture
def setup():
    app = create_app(
        Settings(
            "sqlite:///:memory:",
            "redis://localhost:6379/0",
            {"old": os.urandom(32)},
            "old",
            "testing",
        )
    )
    engine = app.extensions["engine"]
    Base.metadata.create_all(engine)
    with transaction(engine) as db:
        a, b = Workspace(name="A"), Workspace(name="B")
        owner, other, staff = (
            User(name="Owner"),
            User(name="Other"),
            User(name="Staff", is_staff=True),
        )
        db.add_all([a, b, owner, other, staff])
        db.flush()
        db.add_all(
            [
                Membership(user_id=owner.id, workspace_id=a.id, role="owner"),
                Membership(user_id=other.id, workspace_id=b.id, role="viewer"),
            ]
        )
        tokens = {
            name: issue_session(db, user.id)
            for name, user in [("a", owner), ("b", other), ("staff", staff)]
        }
        ids = {"a": a.id, "b": b.id, "user": owner.id}
    yield app, engine, ids, tokens
    engine.dispose()
