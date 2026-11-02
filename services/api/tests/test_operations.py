import json

from sqlalchemy import select

from growth.alerts import collect, deliver
from growth.costs import record_cost
from growth.db import transaction
from growth.models import ApiError, CostAlert, User


def auth(token):
    return {"Authorization": "Bearer " + token}


def test_sanitized_errors_visible_only_to_staff(setup):
    app, engine, ids, tokens = setup

    @app.get("/test/failure/<secret>")
    def failure(secret):
        raise RuntimeError("private-exception-text:" + secret)

    client = app.test_client()
    response = client.get(
        "/test/failure/private-value?token=private-query",
        headers={**auth(tokens["a"]), "X-Secret": "private-header"},
    )
    assert response.status_code == 500
    with transaction(engine) as db:
        record = db.scalar(select(ApiError))
        assert record.request_id == response.headers["X-Request-ID"]
        assert record.route == "/test/failure/<secret>"
        assert "private-" not in json.dumps(
            {key: getattr(record, key) for key in ("route", "code")}
        )
    assert client.get("/v1/admin/api-errors", headers=auth(tokens["a"])).status_code == 403
    result = client.get("/v1/admin/api-errors", headers=auth(tokens["staff"]))
    assert len(result.json["items"]) == 1
    assert "private-" not in result.get_data(as_text=True)


def test_admin_pagination_does_not_silently_drop_records(setup):
    app, engine, _, tokens = setup
    with transaction(engine) as db:
        db.add_all([User(name=f"page-{index}") for index in range(105)])
    client = app.test_client()
    ids = set()
    cursor = ""
    while True:
        result = client.get(
            "/v1/admin/users?limit=30&after=" + cursor, headers=auth(tokens["staff"])
        )
        assert result.status_code == 200
        for row in result.json["items"]:
            assert row["id"] not in ids
            ids.add(row["id"])
        cursor = result.json["next_cursor"]
        if cursor is None:
            break
    assert len(ids) == 108
    assert client.get("/v1/admin/users?limit=101", headers=auth(tokens["staff"])).status_code == 400


def test_cost_alert_month_dedup_delivery_retry_and_terminal_failure(setup):
    _, engine, ids, _ = setup
    with transaction(engine) as db:
        record_cost(db, ids["a"], "expensive-call", 50000)
    collect(engine)
    collect(engine)
    with transaction(engine) as db:
        rows = list(db.scalars(select(CostAlert)))
        assert len(rows) == 1
        ident = rows[0].id
        rows[0].available_at = 100

    class Sink:
        def __init__(self):
            self.fail = True
            self.sent = []

        def send(self, payload):
            if self.fail:
                raise OSError("private-network-message")
            self.sent.append(payload["id"])

    sink = Sink()
    deliver(engine, sink, now=100)
    with transaction(engine) as db:
        row = db.get(CostAlert, ident)
        assert row.status == "retrying" and row.last_error == "smtp_delivery_failed"
    sink.fail = False
    deliver(engine, sink, now=101)
    assert not sink.sent
    deliver(engine, sink, now=102)
    deliver(engine, sink, now=110)
    assert sink.sent == [ident]
    with transaction(engine) as db:
        db.add(CostAlert(workspace_id=ids["b"], period="2099-01", cost_paise=1, available_at=100))
    sink.fail = True
    for now in (100, 102, 106, 114, 130):
        deliver(engine, sink, now=now)
    with transaction(engine) as db:
        failed = db.scalar(select(CostAlert).where(CostAlert.workspace_id == ids["b"]))
        assert failed.status == "failed" and failed.attempts == 5
