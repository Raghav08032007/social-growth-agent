# Growth foundation API

Flask application factory, SQLAlchemy models, reversible Alembic migrations, opaque revocable sessions, tenant membership checks, AES-GCM envelope vault, durable job outbox, Celery dispatcher/worker, Redis atomic limiter and staff cost telemetry.

See [setup](../../docs/foundation-setup.md) and [phase plan](../../docs/plans/phase-0.md). No public signup, model calls, social API calls or customer payments are implemented in this module. The earlier local demo is a separate application.

Routes:

The full machine-readable contract is `/openapi.json` (also checked against Flask's routes). Staff record collections now paginate with `limit` and `after`; the overview is a summary, not a substitute for cursor traversal. Error records omit request values and exception text. Alert delivery is at least once, with stable Message-ID and bounded retry; development mail stays in Mailpit.

| Route | Access | Result |
|---|---|---|
| GET /health/live | public | liveness |
| GET /health/ready | public | MySQL/schema/Redis readiness |
| GET /v1/workspaces | session | own workspaces and user |
| GET /v1/workspaces/current/{flags,audit,usage,jobs,connections} | session + membership | safe fields, cursor pagination |
| GET /v1/workspaces/current/summary | session + membership | complete counts and current UTC-month AI cost |
| POST /v1/jobs/diagnostic | owner/manager; non-production | durable diagnostic job; requires Idempotency-Key |
| DELETE /v1/session | session | revoke current session |
| GET /v1/admin/overview | staff | capped global workspace cost/users/dead-letter lists |

All errors use `error.code`, `error.message`, `error.request_id`; responses include `X-Request-ID`. Secrets, token envelopes and contact details are not returned by operational collection routes. Data costs are integer paise and explicitly diagnostic until real model metering is wired. Database triggers forbid audit/cost updates and deletes; refunds and corrections must append compensating records when those workflows are implemented.
