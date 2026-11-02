import base64
import json
import os

import pytest
from sqlalchemy import select

from growth.costs import record_cost
from growth.db import transaction
from growth.jobs import enqueue, execute
from growth.models import (
    AgentAction,
    CreditEntry,
    FeatureFlag,
    Job,
    SessionToken,
    VaultToken,
    timestamp,
)
from growth.security import Problem, digest
from growth.vault import EnvironmentKeyProvider, Vault


def headers(token, workspace=None):
    return {
        "Authorization": "Bearer " + token,
        **({"X-Workspace-ID": workspace} if workspace else {}),
    }


def test_session_auth_expiry_revocation_and_no_header_impersonation(setup):
    app, engine, ids, tokens = setup
    client = app.test_client()
    assert client.get("/v1/workspaces").status_code == 401
    assert client.get("/v1/workspaces", headers={"X-Workspace-ID": ids["a"]}).status_code == 401
    owned = client.get("/v1/workspaces", headers=headers(tokens["a"])).json
    assert [row["id"] for row in owned["workspaces"]] == [ids["a"]]
    with transaction(engine) as db:
        row = db.get(SessionToken, digest(tokens["a"]))
        assert row.token_hash != tokens["a"]
        row.expires_at = timestamp() - 1
    assert client.get("/v1/workspaces", headers=headers(tokens["a"])).status_code == 401
    assert client.delete("/v1/session", headers=headers(tokens["b"])).status_code == 204
    assert client.get("/v1/workspaces", headers=headers(tokens["b"])).status_code == 401


def test_five_tenant_collections_and_related_writes_are_isolated(setup):
    app, engine, ids, tokens = setup
    vault = app.extensions["vault"]
    with transaction(engine) as db:
        db.add(FeatureFlag(workspace_id=ids["b"], name="foreign-only", enabled=True))
        db.add(
            AgentAction(
                workspace_id=ids["b"], actor_id="fixture", action="foreign-only", entity_id="x"
            )
        )
        record_cost(db, ids["b"], "foreign-only", 25)
        enqueue(db, ids["b"], "foreign-only", "diagnostic.retry", {"fail_until": 0})
        foreign = vault.store(db, ids["b"], "fixture", "account", "secret-never-returned", [])
    client = app.test_client()
    for collection in ("flags", "audit", "usage", "jobs", "connections"):
        own = client.get(
            f"/v1/workspaces/current/{collection}", headers=headers(tokens["a"], ids["a"])
        )
        assert own.status_code == 200 and own.json == {"items": [], "next_cursor": None}
        assert (
            client.get(
                f"/v1/workspaces/current/{collection}", headers=headers(tokens["a"], ids["b"])
            ).status_code
            == 403
        )
    assert (
        client.post(
            "/v1/jobs/diagnostic",
            json={"fail_until": 0},
            headers={**headers(tokens["a"], ids["b"]), "Idempotency-Key": "x"},
        ).status_code
        == 403
    )
    with transaction(engine) as db, pytest.raises(Problem):
        vault.read(db, ids["a"], foreign)


def test_envelope_tamper_rotation_and_revoke(setup):
    app, engine, ids, tokens = setup
    vault = app.extensions["vault"]
    old_key = app.extensions["settings"].vault_keys["old"]
    new_key = os.urandom(32)
    rotated = Vault(EnvironmentKeyProvider({"old": old_key, "new": new_key}, "new"))
    only_new = Vault(EnvironmentKeyProvider({"new": new_key}, "new"))
    with transaction(engine) as db:
        ident = vault.store(db, ids["a"], "fixture", "acct", "private-token-value", ["read"])
        row = db.get(VaultToken, ident)
        assert "private-token-value" not in json.dumps(row.envelope)
        assert vault.read(db, ids["a"], ident) == "private-token-value"
        with pytest.raises(Problem):
            only_new.read(db, ids["a"], ident)
        rotated.rewrap(db, ids["a"], ident)
        assert only_new.read(db, ids["a"], ident) == "private-token-value"
        good = dict(row.envelope)
        row.envelope = {
            **row.envelope,
            "ciphertext": base64.urlsafe_b64encode(os.urandom(40)).decode(),
        }
        with pytest.raises(Problem):
            rotated.read(db, ids["a"], ident)
        row.envelope = good
        rotated.revoke(db, ids["a"], ident, ids["user"])
        assert row.envelope == {}
        with pytest.raises(Problem):
            rotated.read(db, ids["a"], ident)


def test_job_retry_dead_letter_dedupe_fencing_and_tenant(setup):
    app, engine, ids, tokens = setup
    with transaction(engine) as db:
        row = enqueue(db, ids["a"], "retry", "diagnostic.retry", {"fail_until": 2})
        ident = row.id
        assert enqueue(db, ids["a"], "retry", "diagnostic.retry", {"fail_until": 2}).id == ident
        with pytest.raises(Problem):
            enqueue(db, ids["a"], "retry", "diagnostic.retry", {"fail_until": 1})
        row.available_at = 100
        dead = enqueue(db, ids["a"], "dead", "diagnostic.retry", {"fail_until": 10}).id
        db.get(Job, dead).available_at = 100
    assert execute(engine, ids["b"], ident, 100, 0) == "not_claimed"
    assert execute(engine, ids["a"], ident, 100, 0) == "retrying"
    assert execute(engine, ids["a"], ident, 101, 0) == "not_claimed"
    assert execute(engine, ids["a"], ident, 102, 0) == "retrying"
    assert execute(engine, ids["a"], ident, 106, 0) == "succeeded"
    assert execute(engine, ids["a"], ident, 200, 0) == "not_claimed"
    for at in (100, 102, 106):
        result = execute(engine, ids["a"], dead, at, 0)
    assert result == "dead_letter"
    with transaction(engine) as db:
        assert db.get(Job, ident).attempts == 3


def test_expired_lease_can_be_reclaimed_and_active_lease_cannot(setup):
    _, engine, ids, _ = setup
    with transaction(engine) as db:
        row = enqueue(db, ids["a"], "lease", "diagnostic.retry", {"fail_until": 0})
        ident = row.id
        row.status, row.available_at, row.lease_until = "running", 0, 200
    assert execute(engine, ids["a"], ident, 100, 0) == "not_claimed"
    assert execute(engine, ids["a"], ident, 201, 0) == "succeeded"


def test_staff_cost_alert_and_private_envelopes(setup):
    app, engine, ids, tokens = setup
    with transaction(engine) as db:
        record_cost(db, ids["a"], "cost", 50000)
        record_cost(db, ids["a"], "cost", 50000)
        with pytest.raises(Problem):
            record_cost(db, ids["a"], "cost", 60000)
        assert len(list(db.scalars(select(CreditEntry)))) == 1
    client = app.test_client()
    assert client.get("/v1/admin/overview", headers=headers(tokens["a"])).status_code == 403
    result = client.get("/v1/admin/overview", headers=headers(tokens["staff"]))
    assert result.status_code == 200
    row = next(row for row in result.json["workspaces"] if row["workspace_id"] == ids["a"])
    assert row["ai_cost_paise"] == 50000 and row["alert"] is True
    assert "envelope" not in result.get_data(as_text=True)
    own = client.get("/v1/workspaces/current/summary", headers=headers(tokens["a"], ids["a"]))
    assert own.status_code == 200 and own.json["ai_cost_paise"] == 50000
    assert (
        client.get(
            "/v1/workspaces/current/summary", headers=headers(tokens["a"], ids["b"])
        ).status_code
        == 403
    )


def test_collection_pagination_never_leaks_other_workspaces(setup):
    app, engine, ids, tokens = setup
    with transaction(engine) as db:
        for index in range(3):
            db.add(FeatureFlag(workspace_id=ids["a"], name=f"own-{index}", enabled=True))
            db.add(FeatureFlag(workspace_id=ids["b"], name=f"foreign-{index}", enabled=True))
    client = app.test_client()
    first = client.get(
        "/v1/workspaces/current/flags?limit=2", headers=headers(tokens["a"], ids["a"])
    )
    assert len(first.json["items"]) == 2 and first.json["next_cursor"]
    second = client.get(
        "/v1/workspaces/current/flags?limit=2&after=" + first.json["next_cursor"],
        headers=headers(tokens["a"], ids["a"]),
    )
    assert len(second.json["items"]) == 1 and second.json["next_cursor"] is None
    assert all(row["name"].startswith("own-") for row in first.json["items"] + second.json["items"])
    assert (
        client.get(
            "/v1/workspaces/current/flags?limit=101", headers=headers(tokens["a"], ids["a"])
        ).status_code
        == 400
    )


def test_job_api_roles_validation_and_error_format(setup):
    app, _, ids, tokens = setup
    client = app.test_client()
    auth = {**headers(tokens["a"], ids["a"]), "Idempotency-Key": "one"}
    assert (
        client.post("/v1/jobs/diagnostic", json={"fail_until": 2}, headers=auth).status_code == 202
    )
    conflict = client.post("/v1/jobs/diagnostic", json={"fail_until": 1}, headers=auth)
    assert conflict.status_code == 409
    assert conflict.json["error"]["request_id"] == conflict.headers["X-Request-ID"]
    assert client.post("/v1/jobs/diagnostic", json=[], headers=auth).status_code == 400
    assert (
        client.post("/v1/jobs/diagnostic", json={"fail_until": True}, headers=auth).status_code
        == 400
    )
    assert (
        client.post(
            "/v1/jobs/diagnostic", json={"fail_until": 0}, headers=headers(tokens["b"], ids["b"])
        ).status_code
        == 403
    )
    assert client.get("/missing").is_json
