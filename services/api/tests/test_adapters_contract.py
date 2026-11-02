import re
import smtplib
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import select

from growth.adapters import (
    Capability,
    CapabilityRegistry,
    ModelUsage,
    UnconfiguredProvider,
    meter_model_usage,
)
from growth.alerts import SMTPNotifier
from growth.db import transaction
from growth.models import CreditEntry
from growth.security import Problem


def test_capabilities_fail_closed_and_require_verified_scope():
    entry = Capability(
        "fixture",
        "publish",
        frozenset({"fixture.write"}),
        "https://example.test/contract",
        "test",
        True,
    )
    registry = CapabilityRegistry([entry])
    assert registry.require("fixture", "publish", ["fixture.write"]) == entry
    with pytest.raises(Problem):
        registry.require("fixture", "publish", [])
    with pytest.raises(Problem):
        registry.require("unknown", "publish", [])
    with pytest.raises(Problem):
        CapabilityRegistry([Capability("fixture", "read", frozenset(), "", "test")]).require(
            "fixture", "read", []
        )
    with pytest.raises(Problem):
        UnconfiguredProvider().generate("id", "prompt")


def test_model_meter_rounding_dedup_and_invalid_usage(setup):
    _, engine, ids, _ = setup
    with transaction(engine) as db:
        args = dict(input_paise_per_million=100000, output_paise_per_million=200000)
        first = meter_model_usage(db, ids["a"], "provider-request", ModelUsage(3, 2), **args)
        assert (
            meter_model_usage(db, ids["a"], "provider-request", ModelUsage(3, 2), **args) == first
        )
        assert db.get(CreditEntry, first).amount_paise == 1
        with pytest.raises(Problem):
            meter_model_usage(db, ids["a"], "bad", ModelUsage(-1, 0), **args)
        assert len(list(db.scalars(select(CreditEntry)))) == 1


def test_smtp_transport_tls_auth_message_identity_and_refusal():
    transport = MagicMock()
    transport.__enter__.return_value = transport
    transport.send_message.return_value = {}
    payload = {"id": "a" * 32, "workspace_id": "b" * 32, "period": "2026-11", "cost_paise": 123}
    notifier = SMTPNotifier(
        "fixture",
        1025,
        "sender@example.test",
        "recipient@example.test",
        tls=True,
        username="u",
        password="p",
    )
    with patch("growth.alerts.smtplib.SMTP", return_value=transport):
        notifier.send(payload)
        transport.starttls.assert_called_once()
        transport.login.assert_called_once_with("u", "p")
        message = transport.send_message.call_args.args[0]
        assert message["Message-ID"] == "<cost-alert-" + payload["id"] + "@social-growth.local>"
        assert "INR 1.23" in message.get_content()
        transport.send_message.return_value = {"recipient@example.test": (550, b"rejected")}
        with pytest.raises(smtplib.SMTPRecipientsRefused):
            notifier.send(payload)


def test_openapi_covers_every_route_and_auth_contract(setup):
    app, _, _, _ = setup
    response = app.test_client().get("/openapi.json")
    assert response.status_code == 200
    spec = response.json
    assert spec["security"] == [{"BearerSession": []}]
    for route in app.url_map.iter_rules():
        path = re.sub(r"<([^>]+)>", r"{\1}", route.rule)
        assert path in spec["paths"], path
        for method in route.methods - {"HEAD", "OPTIONS"}:
            assert method.lower() in spec["paths"][path]
