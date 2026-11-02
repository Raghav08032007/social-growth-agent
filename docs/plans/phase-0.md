# Phase 0 implementation plan

Start: 2 November 2026. Scope: PL-3, PL-5, PL-7, PL-8. Original feature IDs are preserved. The existing stdlib demo stays separate from the production foundation.

## First implementation

Create `services/api` (Flask application factory, SQLAlchemy, Alembic, Celery) and `frontend` (React/Vite/TypeScript shell). Add a MySQL/Redis Compose development stack and repeatable checks. Use SQLite only for fast isolated tests; MySQL/Redis integration verification is a separate gate.

| Feature | User story / data and service | UI | Required evidence / risks |
|---|---|---|---|
| PL-3 | Workspace member sees only permitted workspace data; users, memberships, flags and revocable hashed opaque sessions provisioned through CLI until P1 sign-in | responsive navigation, en/ta/hi shell strings, theme, installable manifest; session token kept in memory | build/typecheck, browser 360px, authorization tests; translations are initial strings pending native review |
| PL-5 | Service encrypts connector secrets with random per-record data keys wrapped by versioned environment master key; rotate/rewrap and revoke locally | status only; no raw token API | wrong tenant, altered envelope, unknown/rotated keys, revoked secrets; provider refresh/revoke waits for real P1 adapters |
| PL-7 | Workspace jobs have idempotency, lease, retry/backoff/jitter and dead-letter state; DB outbox dispatcher routes Celery; Redis atomic per-account/endpoint limiter | job state/failure counts | retries twice then succeeds, permanent failure dead letters, dedupe conflict, expired lease, Redis integration; no real side-effect jobs yet |
| PL-8 | Scoped staff reads users/workspaces, failed jobs and metered cost; nonstaff denied; usage ledger holds integer paise and configurable cost ratio | authenticated staff operations page | cost alert from explicit fixture event, cross-tenant list denial, staff denial; cost ingestion initially internal only |

## Access boundary

P0 has no public signup. A local CLI provisions a user/workspace/session and prints an opaque session token once. Database stores only token hash and expiry. Requests select a workspace via header but server checks authenticated membership. No universal admin token, no automatic demo account, no unauthenticated provisioning route. Public signup/Google/OTP remain P1. Staff identity is an explicit CLI flag and staff reads never include token ciphertext or secrets.

## Data and migrations

Versioned migrations for users, workspaces, memberships, sessions, feature_flags, vault_tokens, agent_actions, credits_ledger and job_log. Tenant services require workspace ID and all reads/updates include it. User/membership/session tables are identity scope. Migration upgrade/downgrade tested from empty database; services must refuse uninitialized schema instead of creating it on HTTP startup.

## Failure and testing

Fail startup on missing keys/unsupported environment. Return common JSON errors/request IDs, reject unknown routes, limit request bodies, avoid plaintext secret/PII logs. All unsafe actions require valid session + workspace + role. Money/costs are integer paise. Jobs use unique tenant/idempotency keys; payload conflict gives 409. Job IDs on broker contain no secrets. Token decryption is internal only and tenant/connection bound. Document exact environment and key loss/rotation recovery.

Run tests appropriate to modules, frontend typecheck/build, existing demo tests and feature inventory checks. Then attempt real MySQL migrations/Redis worker tests via Docker. Report fixture, browser and container results independently. P0 is complete only when all original exit gates pass, including real queue infrastructure, admin costs and mobile language switch. Do not promote a feature merely because its service tests pass.

## Deferred

## Completion pass

Continue P0 with sanitized API-error records, cursor-paginated staff lists, a durable per-workspace/month cost-alert outbox and local SMTP delivery/retry. Add OpenAPI covering every exposed route, internal provider protocols with fail-closed defaults, capability gates and lifecycle contract tests, offline public-shell caching that never caches authenticated responses, storage/mail development dependencies and backup/restore/load diagnostics. Re-run migration, unit, browser and real-container gates. Local acceptance and human/provider launch prerequisites must be reported separately; do not promote whole-phase status while an original gate remains unverified.

P1+ authentication UI flows, real OAuth/provider adapters/refresh, AI generation, publishing, inbox, commerce and billing. No customer messages/payments. This phase builds internal primitives and an operations shell, not live social integrations.
