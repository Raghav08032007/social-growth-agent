import re

from sqlalchemy import select

from growth.db import transaction
from growth.models import CreditEntry, SessionToken, User, Workspace


def test_operator_provision_session_and_revocation(setup):
    app, engine, _, _ = setup
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["provision", "--name", "Operator test", "--workspace", "CLI workspace"]
    )
    assert result.exit_code == 0
    token = re.search(r"Session \(one hour\): (\S+)", result.output).group(1)
    client = app.test_client()
    response = client.get("/v1/workspaces", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json["user"]["is_staff"] is False
    user = response.json["user"]["id"]
    assert runner.invoke(args=["revoke-session"], input=token + "\n").exit_code == 0
    assert (
        client.get("/v1/workspaces", headers={"Authorization": "Bearer " + token}).status_code
        == 401
    )
    replacement = runner.invoke(args=["session", "--user-id", user])
    assert replacement.exit_code == 0
    assert (
        client.get(
            "/v1/workspaces", headers={"Authorization": "Bearer " + replacement.output.strip()}
        ).status_code
        == 200
    )
    assert runner.invoke(args=["session", "--user-id", "missing"]).exit_code != 0
    with transaction(engine) as db:
        assert all(row.token_hash != token for row in db.scalars(select(SessionToken)))
        assert db.get(User, user).is_staff is False


def test_diagnostic_cost_and_rotation_commands(setup):
    app, engine, ids, _ = setup
    runner = app.test_cli_runner()
    args = [
        "record-diagnostic-cost",
        "--workspace-id",
        ids["a"],
        "--operation-key",
        "cli",
        "--amount-paise",
        "17",
    ]
    assert runner.invoke(args=args).exit_code == 0
    assert runner.invoke(args=args).exit_code == 0
    assert runner.invoke(args=["rotate-vault"]).exit_code == 0
    assert (
        runner.invoke(
            args=[
                "configure-cost-policy",
                "--workspace-id",
                ids["a"],
                "--plan-price-paise",
                "99900",
                "--alert-percent",
                "20",
            ]
        ).exit_code
        == 0
    )
    with transaction(engine) as db:
        assert len(list(db.scalars(select(CreditEntry)))) == 1
        assert db.get(Workspace, ids["a"]).name == "A"
        assert db.get(Workspace, ids["a"]).cost_alert_percent == 20
