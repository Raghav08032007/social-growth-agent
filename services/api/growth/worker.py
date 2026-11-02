import os

from celery import Celery
from redis import Redis
from sqlalchemy import or_, select

from .alerts import SMTPNotifier, collect, deliver
from .config import Settings
from .db import make_engine, transaction
from .jobs import execute
from .limiter import acquire
from .models import Job, timestamp

settings = Settings.from_env()
engine = make_engine(settings.database_url)
redis = Redis.from_url(settings.redis_url, socket_connect_timeout=3, socket_timeout=3)
celery = Celery("growth", broker=settings.redis_url)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_ignore_result=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=45,
    task_time_limit=55,
    broker_transport_options={"visibility_timeout": 90},
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "dispatch-durable-outbox": {"task": "growth.dispatch", "schedule": 2.0},
        "cost-monitor": {"task": "growth.monitor_costs", "schedule": 15.0},
    },
)


@celery.task(name="growth.run_job")
def run_job(workspace, job_id):
    # Infrastructure failure before claim leaves durable DB work available for dispatch.
    if acquire(redis, workspace, "diagnostic", "run_job", capacity=10, refill_per_second=1):
        execute(engine, workspace, job_id)


@celery.task(name="growth.dispatch")
def dispatch():
    # Duplicate broker deliveries are safe: execution claims are atomic and fenced.
    # A DB row remains until success/dead-letter, so broker outage cannot lose work.
    now = timestamp()
    with transaction(engine) as db:
        rows = list(
            db.scalars(
                select(Job)
                .where(
                    Job.available_at <= now,
                    or_(
                        Job.status.in_(["queued", "retrying"]),
                        (Job.status == "running") & (Job.lease_until <= now),
                    ),
                )
                .limit(100)
            )
        )
        for row in rows:
            run_job.delay(row.workspace_id, row.id)


@celery.task(name="growth.monitor_costs")
def monitor_costs():
    collect(engine)
    host, recipient = os.environ.get("ALERT_SMTP_HOST"), os.environ.get("ALERT_TO")
    if host and recipient:
        deliver(
            engine,
            SMTPNotifier(
                host,
                int(os.environ.get("ALERT_SMTP_PORT", "1025")),
                os.environ.get("ALERT_FROM", "operations@social-growth.local"),
                recipient,
                tls=os.environ.get("ALERT_SMTP_TLS") == "1",
                username=os.environ.get("ALERT_SMTP_USER", ""),
                password=os.environ.get("ALERT_SMTP_PASSWORD", ""),
            ),
        )
