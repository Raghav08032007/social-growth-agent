"""Validate a disposable restored schema. Never point workers at this database."""

import json
import re
import sys

from sqlalchemy.engine import make_url

from growth.config import Settings
from growth.db import make_engine, transaction
from growth.jobs import execute
from growth.models import Job
from growth.vault import EnvironmentKeyProvider, Vault

name, workspace, token_id, job_id = sys.argv[1:]
if not re.fullmatch(r"growth_restore_[0-9a-f]{32}", name):
    raise SystemExit("Refusing non-diagnostic database name")
settings = Settings.from_env()
engine = make_engine(
    make_url(settings.database_url).set(database=name).render_as_string(hide_password=False)
)
vault = Vault(EnvironmentKeyProvider(settings.vault_keys, settings.active_key))
with transaction(engine) as db:
    assert vault.read(db, workspace, token_id) == "recovery-fixture-not-a-real-token"
    row = db.get(Job, job_id)
    assert row.workspace_id == workspace and row.status == "queued"
    due = row.available_at
assert execute(engine, workspace, job_id, now=due, jitter=0) == "succeeded"
assert execute(engine, workspace, job_id, now=due + 1, jitter=0) == "not_claimed"
with transaction(engine) as db:
    assert db.get(Job, job_id).attempts == 1
engine.dispose()
print(json.dumps({"restore": "passed", "vault_decryption": "passed", "durable_job_replay": "once"}))
