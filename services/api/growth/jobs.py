"""Durable job outbox and fenced execution. Only local diagnostics are registered in P0."""

import hashlib
import json
import random
import uuid

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError

from .db import transaction
from .models import Job, timestamp
from .security import Problem


def enqueue(db, workspace, key, kind, payload, max_attempts=3):
    if not isinstance(key, str) or not 1 <= len(key) <= 100:
        raise Problem("validation", "Idempotency-Key must contain 1–100 characters")
    key = hashlib.sha256(key.encode()).hexdigest()
    if kind != "diagnostic.retry" or set(payload) != {"fail_until"}:
        raise Problem("validation", "Unregistered job type or invalid diagnostic payload")
    if type(payload["fail_until"]) is not int or not 0 <= payload["fail_until"] <= 10:
        raise Problem("validation", "fail_until must be an integer from 0 to 10")
    row = db.scalar(select(Job).where(Job.workspace_id == workspace, Job.idempotency_key == key))
    if row is None:
        try:
            with db.begin_nested():
                row = Job(
                    workspace_id=workspace,
                    idempotency_key=key,
                    kind=kind,
                    payload=payload,
                    max_attempts=max_attempts,
                )
                db.add(row)
                db.flush()
        except IntegrityError:
            row = db.scalar(
                select(Job).where(Job.workspace_id == workspace, Job.idempotency_key == key)
            )
            if row is None:
                raise
    if row.kind != kind or json.dumps(row.payload, sort_keys=True) != json.dumps(
        payload, sort_keys=True
    ):
        raise Problem("idempotency_conflict", "Idempotency key has a different payload", 409)
    return row


def execute(engine, workspace, job_id, now=None, jitter=None):
    """Claim via atomic update, then finalize only with the same lease fencing token."""
    now = timestamp() if now is None else now
    jitter = random.randint(0, 3) if jitter is None else jitter
    lease = uuid.uuid4().hex
    with transaction(engine) as db:
        db.execute(
            update(Job)
            .where(
                Job.id == job_id,
                Job.workspace_id == workspace,
                Job.status == "running",
                Job.lease_until <= now,
                Job.attempts >= Job.max_attempts,
            )
            .values(
                status="dead_letter",
                last_error="lease_expired_at_attempt_limit",
                lease_token=None,
                lease_until=0,
            )
        )
        claim = db.execute(
            update(Job)
            .where(
                Job.id == job_id,
                Job.workspace_id == workspace,
                Job.available_at <= now,
                Job.attempts < Job.max_attempts,
                or_(
                    Job.status.in_(["queued", "retrying"]),
                    (Job.status == "running") & (Job.lease_until <= now),
                ),
            )
            .values(
                status="running", lease_token=lease, lease_until=now + 60, attempts=Job.attempts + 1
            )
        )
        if not claim.rowcount:
            return "not_claimed"
        row = db.get(Job, job_id)
        attempt, kind, payload = row.attempts, row.kind, row.payload
    # Never add external side effects here without provider-level idempotency/reconciliation.
    if kind != "diagnostic.retry":
        error = "unregistered_job"
    elif attempt <= payload.get("fail_until", 0):
        error = "diagnostic_forced_failure"
    else:
        error = None
    with transaction(engine) as db:
        row = db.scalar(
            select(Job)
            .where(
                Job.id == job_id,
                Job.workspace_id == workspace,
                Job.status == "running",
                Job.lease_token == lease,
            )
            .with_for_update()
        )
        if row is None:
            return "lease_lost"
        row.lease_until = 0
        row.lease_token = None
        if error is None:
            row.status, row.last_error = "succeeded", None
        else:
            row.last_error = error
            row.status = "dead_letter" if row.attempts >= row.max_attempts else "retrying"
            row.available_at = now + min(300, 2 ** min(row.attempts, 8)) + jitter
        return row.status
