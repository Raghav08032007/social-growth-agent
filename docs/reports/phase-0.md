# Phase 0 implementation report

Updated 2 November 2026. **Status: in progress; no whole feature or phase declared production complete.**

**Latest:** the [completion-pass report](phase-0-completion-pass.md) supersedes the older gaps below for error monitoring, pagination, local mail/storage, metering contracts, OpenAPI, offline shell and recovery/load tests. Live-provider and human-review gates remain explicit there.

The interface has since received the [dimensional workspace redesign](../design/redesign-report.md), including an original 3D character, motion controls, preview and broader interaction tests. This improves PL-3 but does not close its remaining release gates.

## Implemented and verified

| Feature | Implementation | Evidence | Remaining |
|---|---|---|---|
| PL-3 shell | React/Vite/TypeScript, eight-module navigation, authenticated workspace selector, initial en/ta/hi strings, theme switch, web manifest | production build/typecheck; Chrome at 360px; all three languages; no JS errors | native-language review, full accessibility/offline/PWA validation, screen details in later phases |
| PL-5 vault/access | opaque session hashes, expiry/revocation, membership authorization, per-record AES-GCM data keys wrapped by versioned environment keys, associated-data binding, rewrap/revoke and CLI rotation | tests deny cross-workspace access across five collections; ciphertext/tamper/rotation/revocation checks; MySQL vault diagnostic | managed KMS, provider-specific scope registry, actual refresh and remote revocation adapters |
| PL-7 jobs | durable DB outbox, Celery dispatcher/worker/beat, atomic fenced claims, expiring leases, bounded retry/backoff/jitter, terminal failure state, tenant idempotency, Redis atomic bucket | local state-machine tests; real MySQL/Redis/Celery retry twice then success and permanent failure after three attempts; Redis quota enforced | provider side-effect reconciliation, broader failure/restart drills and account-specific connector limits |
| PL-8 monitoring | staff-only user/workspace/failed-job costs, integer-paise monthly AI usage, duplicate-safe records, configurable operator threshold, append-only DB triggers, UI alerts | staff denial tests; actual database cost alert; CLI and browser checks | actual model meter, API-error dashboard, admin pagination beyond first 100, operational alert delivery |

## Verification

- **12 new API tests pass.** They cover real request handlers, permissions, session expiry/revocation, tenant isolation, encryption, rotation/tampering, state transitions, idempotency conflicts, operator CLI, pagination and migration upgrade/downgrade/re-upgrade.
- New API unit/service coverage is approximately **87%**. Redis/Celery modules are additionally exercised by the separate live stack diagnostic, not included as unit coverage.
- Ruff lint and formatting pass; frontend TypeScript/Vite production build passes.
- Controlled Chrome browser test passes using temporary SQLite and intercepted transport to actual Flask handlers: invalid session, staff alert, language switches, theme, mobile reflow and revocation. Direct browser-over-HTTP coverage remains separate.
- MySQL 8.4 + Redis 7.4 + API + Celery worker + scheduler + Nginx frontend started successfully through Docker Compose. The final live diagnostic passed retry/dead-letter, limiter, vault, staff alert, session, four-concurrent-request deduplication and physical database append-only checks. Nginx frontend and its API-readiness proxy both returned HTTP 200 from inside the stack.
- The original seven demo tests and 257-feature validator remain separate regression checks.

## Corrections found during integration

Docker Hub initially timed out downloading MySQL; retry reused downloaded layers. MySQL binary logging requires stronger privileges to create audit triggers. Compose now uses a migration-only root credential while API/worker use the application database account; runtime processes do not receive the root password. A deployed environment needs reviewed migration/runtime roles and managed secrets, rather than copying development credentials.

The database stores SHA-256 fingerprints for case-sensitive idempotency keys, avoiding MySQL collation ambiguity. MySQL uses READ COMMITTED so conflict recovery can read the committed duplicate without upgrading duplicate-insert locks; a concurrent diagnostic exposed a deadlock in the earlier locking-read approach, which was corrected. Atomic conditional writes and unique constraints enforce invariants. Job claims are lease-fenced; this does not promise exactly-once behavior for future external providers.

## Scope and gaps

No social accounts, live model calls, real messages or customer payments were used. Diagnostic AI costs are explicit fixtures. P0 uses operator-provisioned one-hour sessions; public Google/OTP/magic-link signup remains P1. No fake authentication or demo workspace header is reused by this API.

Optional mail/storage emulators, production adapter interfaces, managed key integration, error-alert delivery, full OpenAPI specification, restore/load drills and the remaining checks above still need implementation. The original P0 exit test is therefore **partially passed**, not complete. P1 work has not begun.

The original source catalogue remains unchanged at 257 planned entries. Current implementation tracking is **four P0 features in progress, zero whole features production complete, 253 features not started**. A single feature contains multiple workflows; these counts do not measure engineering effort.

## Reproduce

See [foundation setup](../foundation-setup.md). Run `python scripts/init_local.py`, `docker compose up --build -d --wait`, then `docker compose exec -T api python check_stack.py`. Use the operator provisioning command to obtain a session for http://127.0.0.1:8080. Environment keys and credentials stay in ignored `.env`; fixture screenshots stay in ignored `artifacts/`.

## Next work

Complete P0 adapter contracts, connector permission registry and error monitoring; add the remaining infrastructure/restore checks and native-language/accessibility review. Only then open P1 onboarding and a real publishing connector. Preserve explicit fixture/sandbox/live evidence for each step.
