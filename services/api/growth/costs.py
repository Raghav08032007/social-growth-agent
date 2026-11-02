import hashlib
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from .models import CreditEntry
from .security import Problem


def record_cost(db, workspace, operation_key, amount_paise, category="ai"):
    if type(amount_paise) is not int or not 0 <= amount_paise <= 100_000_000:
        raise Problem("validation", "Cost must be integer paise within limit")
    if not isinstance(operation_key, str) or not 1 <= len(operation_key) <= 100:
        raise Problem("validation", "Invalid operation key")
    operation_key = hashlib.sha256(operation_key.encode()).hexdigest()
    existing = db.scalar(
        select(CreditEntry).where(
            CreditEntry.workspace_id == workspace, CreditEntry.operation_key == operation_key
        )
    )
    if existing:
        if existing.amount_paise != amount_paise or existing.category != category:
            raise Problem("idempotency_conflict", "Cost operation payload differs", 409)
        return existing.id
    try:
        with db.begin_nested():
            row = CreditEntry(
                workspace_id=workspace,
                operation_key=operation_key,
                amount_paise=amount_paise,
                category=category,
            )
            db.add(row)
            db.flush()
    except IntegrityError:
        row = db.scalar(
            select(CreditEntry).where(
                CreditEntry.workspace_id == workspace, CreditEntry.operation_key == operation_key
            )
        )
        if row is None:
            raise
        if row.amount_paise != amount_paise or row.category != category:
            raise Problem("idempotency_conflict", "Cost operation payload differs", 409) from None
    return row.id


def summary(db, workspace):
    start = int(
        datetime.now(timezone.utc)
        .replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )
    cost = db.scalar(
        select(func.coalesce(func.sum(CreditEntry.amount_paise), 0)).where(
            CreditEntry.workspace_id == workspace.id,
            CreditEntry.created_at >= start,
            CreditEntry.category == "ai",
        )
    )
    return {
        "workspace_id": workspace.id,
        "name": workspace.name,
        "ai_cost_paise": int(cost),
        "plan_price_paise": workspace.plan_price_paise,
        "alert_percent": workspace.cost_alert_percent,
        "alert": cost * 100 > workspace.plan_price_paise * workspace.cost_alert_percent,
        "period": datetime.now(timezone.utc).strftime("%Y-%m"),
    }
