"""Live MySQL + Redis + Celery diagnostic. Creates only uniquely named fixture records."""

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from redis import Redis
from sqlalchemy import delete, select
from sqlalchemy.exc import DBAPIError

from growth import create_app
from growth.costs import record_cost
from growth.db import transaction
from growth.jobs import enqueue
from growth.limiter import acquire
from growth.models import CreditEntry, Job, Membership, User, Workspace
from growth.models import CostAlert
from growth.security import issue_session
from growth.vault import EnvironmentKeyProvider, Vault


def main():
    app = create_app()
    engine = app.extensions["engine"]
    settings = app.extensions["settings"]
    key = uuid.uuid4().hex

    @app.get("/diagnostics/fixture-failure")
    def fixture_failure():
        raise RuntimeError("fixture-private-error-must-not-be-stored")

    with transaction(engine) as db:
        workspace = Workspace(name="Integration diagnostic " + key[:8])
        user = User(name="Integration staff", is_staff=True)
        db.add_all([workspace, user])
        db.flush()
        wid = workspace.id
        uid = user.id
        db.add(Membership(user_id=user.id, workspace_id=wid, role="owner"))
        session = issue_session(db, user.id)
        success = enqueue(db, wid, key + "-retry", "diagnostic.retry", {"fail_until": 2}).id
        failure = enqueue(db, wid, key + "-dead", "diagnostic.retry", {"fail_until": 10}).id
        record_cost(db, wid, key, 50000)
        vault = app.extensions["vault"]
        token_id = vault.store(db, wid, "diagnostic", key, "fixture-not-a-provider-token", [])
    redis = Redis.from_url(settings.redis_url)

    def duplicate_request(_):
        with transaction(engine) as db:
            job = enqueue(db, wid, key + "-concurrent", "diagnostic.retry", {"fail_until": 0})
            cost_id = record_cost(db, wid, key + "-concurrent", 1, category="diagnostic")
            return job.id, cost_id

    with ThreadPoolExecutor(max_workers=4) as pool:
        duplicate_results = list(pool.map(duplicate_request, range(4)))
    assert len(set(duplicate_results)) == 1, "Concurrent duplicate created extra records"
    try:
        with transaction(engine) as db:
            db.execute(delete(CreditEntry).where(CreditEntry.workspace_id == wid))
    except DBAPIError:
        pass
    else:
        raise AssertionError("Database allowed deletion of immutable cost entries")
    assert acquire(redis, wid, key, "check", capacity=1, refill_per_second=0.01)
    assert not acquire(redis, wid, key, "check", capacity=1, refill_per_second=0.01)
    with transaction(engine) as db:
        import os

        rotated = Vault(
            EnvironmentKeyProvider(
                {**settings.vault_keys, "diagnostic": os.urandom(32)}, "diagnostic"
            )
        )
        rotated.rewrap(db, wid, token_id)
        assert rotated.read(db, wid, token_id) == "fixture-not-a-provider-token"
        # Restore environment-key wrapping so no record relies on an ephemeral test key.
        restored = Vault(EnvironmentKeyProvider(rotated.provider.keys, settings.active_key))
        restored.rewrap(db, wid, token_id)
        vault.revoke(db, wid, token_id, uid)
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        with transaction(engine) as db:
            rows = list(db.scalars(select(Job).where(Job.id.in_([success, failure]))))
            states = {row.id: (row.status, row.attempts) for row in rows}
        if states.get(success) == ("succeeded", 3) and states.get(failure) == ("dead_letter", 3):
            break
        time.sleep(1)
    else:
        raise AssertionError(f"Worker outcomes not reached: {states}")
    client = app.test_client()
    assert client.get("/diagnostics/fixture-failure").status_code == 500
    response = client.get("/v1/admin/overview", headers={"Authorization": "Bearer " + session})
    assert response.status_code == 200
    entry = next(row for row in response.json["workspaces"] if row["workspace_id"] == wid)
    assert entry["alert"] and entry["ai_cost_paise"] == 50000
    assert any(row["id"] == failure for row in response.json["failed_jobs"])
    assert any(
        row["route"] == "/diagnostics/fixture-failure" for row in response.json["api_errors"]
    )
    assert "fixture-private-error" not in response.get_data(as_text=True)
    deadline = time.monotonic() + 60
    alert_id = None
    while time.monotonic() < deadline:
        with transaction(engine) as db:
            alert = db.scalar(select(CostAlert).where(CostAlert.workspace_id == wid))
            if alert and alert.status == "delivered":
                alert_id = alert.id
                break
        time.sleep(1)
    assert alert_id, "Local cost alert was not delivered"
    import urllib.request

    messages = json.load(urllib.request.urlopen("http://mailpit:8025/api/v1/messages", timeout=5))
    assert any("cost-alert-" + alert_id in message["MessageID"] for message in messages["messages"])
    assert client.get("/health/ready").status_code == 200
    assert (
        client.delete("/v1/session", headers={"Authorization": "Bearer " + session}).status_code
        == 204
    )
    print(
        json.dumps(
            {
                "result": "passed",
                "database": "MySQL",
                "queue": "Redis/Celery",
                "retry_attempts": 3,
                "terminal_failure_attempts": 3,
                "rate_limit": "enforced",
                "vault": "rewrapped and revoked",
                "cost_alert": True,
                "session": "revoked",
                "concurrent_deduplication": "passed",
                "database_append_only": "enforced",
                "api_error_redaction": "passed",
                "local_smtp_alert": "delivered",
            }
        )
    )


if __name__ == "__main__":
    main()
