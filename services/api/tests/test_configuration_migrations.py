import base64
import json
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from growth.config import Settings
from growth.db import make_engine, transaction
from growth.models import AgentAction, CreditEntry, Workspace


def test_missing_and_invalid_configuration_fails_closed(monkeypatch):
    for name in ("DATABASE_URL", "REDIS_URL", "VAULT_KEYS", "VAULT_ACTIVE_KEY"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValueError):
        Settings.from_env()
    monkeypatch.setenv("VAULT_KEYS", "{broken")
    with pytest.raises(ValueError):
        Settings.from_env()
    monkeypatch.setenv(
        "VAULT_KEYS", json.dumps({"v1": base64.urlsafe_b64encode(os.urandom(32)).decode()})
    )
    monkeypatch.setenv("VAULT_ACTIVE_KEY", "v1")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    assert Settings.from_env().active_key == "v1"
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_versioned_migration_upgrade_downgrade_roundtrip(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    url = "sqlite:///" + (tmp_path / "migration.sqlite3").as_posix()
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("VAULT_ACTIVE_KEY", "test")
    monkeypatch.setenv(
        "VAULT_KEYS", json.dumps({"test": base64.urlsafe_b64encode(os.urandom(32)).decode()})
    )
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    command.upgrade(config, "head")
    engine = make_engine(url)
    tables = inspect(engine).get_table_names()
    assert {
        "users",
        "workspaces",
        "memberships",
        "sessions",
        "feature_flags",
        "vault_tokens",
        "agent_actions",
        "credits_ledger",
        "job_log",
    } <= set(tables)
    with transaction(engine) as db:
        workspace = Workspace(name="Immutable fixture")
        db.add(workspace)
        db.flush()
        db.add(
            CreditEntry(
                workspace_id=workspace.id, operation_key="fixture", amount_paise=1, category="ai"
            )
        )
        db.add(
            AgentAction(
                workspace_id=workspace.id, actor_id="fixture", entity_id="fixture", action="fixture"
            )
        )
    for table in ("credits_ledger", "agent_actions"):
        with pytest.raises(DBAPIError), engine.begin() as db:
            db.execute(text(f"DELETE FROM {table}"))
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    command.upgrade(config, "head")
    command.check(config)
    engine.dispose()
