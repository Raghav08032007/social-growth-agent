"""Cost alert outbox. At-least-once SMTP delivery uses a stable Message-ID."""

import smtplib
import uuid
from email.message import EmailMessage

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError

from .costs import summary
from .db import transaction
from .models import CostAlert, Workspace, timestamp


def collect(engine):
    with transaction(engine) as db:
        cursor = ""
        while True:
            workspaces = list(
                db.scalars(
                    select(Workspace).where(Workspace.id > cursor).order_by(Workspace.id).limit(100)
                )
            )
            if not workspaces:
                break
            cursor = workspaces[-1].id
            for workspace in workspaces:
                value = summary(db, workspace)
                if not value["alert"]:
                    continue
                exists = db.scalar(
                    select(CostAlert.id).where(
                        CostAlert.workspace_id == workspace.id, CostAlert.period == value["period"]
                    )
                )
                if exists:
                    continue
                try:
                    with db.begin_nested():
                        db.add(
                            CostAlert(
                                workspace_id=workspace.id,
                                period=value["period"],
                                cost_paise=value["ai_cost_paise"],
                            )
                        )
                        db.flush()
                except IntegrityError:
                    # Another collector wrote the same tenant/month; the outbox is already durable.
                    pass


class SMTPNotifier:
    def __init__(self, host, port, sender, recipient, *, tls=False, username="", password=""):
        self.host, self.port, self.sender, self.recipient = host, port, sender, recipient
        self.tls, self.username, self.password = tls, username, password

    def send(self, alert):
        message = EmailMessage()
        message["From"], message["To"] = self.sender, self.recipient
        message["Subject"] = "Social Growth: workspace AI cost threshold exceeded"
        message["Message-ID"] = f"<cost-alert-{alert['id']}@social-growth.local>"
        message.set_content(
            f"Workspace ID: {alert['workspace_id']}\nPeriod: {alert['period']}\n"
            f"Recorded AI cost: INR {alert['cost_paise'] / 100:.2f}\n"
            "Review the staff Operations page. This is a monitoring alert."
        )
        with smtplib.SMTP(self.host, self.port, timeout=8) as client:
            if self.tls:
                import ssl

                client.starttls(context=ssl.create_default_context())
            if self.username:
                client.login(self.username, self.password)
            rejected = client.send_message(message)
            if rejected:
                raise smtplib.SMTPRecipientsRefused(rejected)


def deliver(engine, notifier, *, now=None):
    now = timestamp() if now is None else now
    # Worklist is bounded; pending rows remain durable for the next dispatch.
    with transaction(engine) as db:
        ids = list(
            db.scalars(
                select(CostAlert.id)
                .where(
                    CostAlert.available_at <= now,
                    or_(
                        CostAlert.status.in_(["pending", "retrying"]),
                        (CostAlert.status == "sending") & (CostAlert.lease_until <= now),
                    ),
                )
                .limit(50)
            )
        )
    for ident in ids:
        lease = uuid.uuid4().hex
        with transaction(engine) as db:
            db.execute(
                update(CostAlert)
                .where(
                    CostAlert.id == ident,
                    CostAlert.status == "sending",
                    CostAlert.lease_until <= now,
                    CostAlert.attempts >= 5,
                )
                .values(
                    status="failed",
                    lease_until=0,
                    lease_token=None,
                    last_error="lease_expired_at_attempt_limit",
                )
            )
            claimed = db.execute(
                update(CostAlert)
                .where(
                    CostAlert.id == ident,
                    CostAlert.attempts < 5,
                    CostAlert.available_at <= now,
                    or_(
                        CostAlert.status.in_(["pending", "retrying"]),
                        (CostAlert.status == "sending") & (CostAlert.lease_until <= now),
                    ),
                )
                .values(
                    status="sending",
                    attempts=CostAlert.attempts + 1,
                    lease_until=now + 60,
                    lease_token=lease,
                )
            )
            if not claimed.rowcount:
                continue
            row = db.get(CostAlert, ident)
            payload = {
                key: getattr(row, key) for key in ("id", "workspace_id", "period", "cost_paise")
            }
        error = None
        try:
            notifier.send(payload)
        except (OSError, smtplib.SMTPException):
            error = "smtp_delivery_failed"
        with transaction(engine) as db:
            row = db.scalar(
                select(CostAlert)
                .where(
                    CostAlert.id == ident,
                    CostAlert.lease_token == lease,
                    CostAlert.status == "sending",
                )
                .with_for_update()
            )
            if row is None:
                continue
            row.lease_until, row.lease_token = 0, None
            if error is None:
                row.status, row.delivered_at, row.last_error = "delivered", now, None
            else:
                row.status = "failed" if row.attempts >= 5 else "retrying"
                row.available_at, row.last_error = now + min(300, 2**row.attempts), error
