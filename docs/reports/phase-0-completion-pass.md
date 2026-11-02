# Phase 0 completion pass

This closes additional local engineering work. It does not certify a production-complete phase or live provider integration.

## Implemented

- Sanitized API-error records: route template, method, status, safe code and request ID. No bodies, headers, query strings, secrets or exception text.
- Staff cursor pagination and UI record browsing for users, workspaces, failed jobs, errors and alert delivery.
- Durable monthly tenant cost alerts: deduplication, atomic leases, bounded retries, terminal failure and local SMTP delivery with stable Message-ID. Delivery is at least once; acknowledgement loss may duplicate email.
- Model token-usage metering: explicit configured prices, integer paise, request deduplication and combined-cost rounding. No real model or current vendor price is claimed.
- Provider/key/storage contracts, unconfigured-provider errors and capability gates that deny unknown/unverified actions.
- OpenAPI 3.1 for every exposed route, with a route-coverage test.
- Public-shell offline caching and PNG install icons. APIs, health responses, authorization-bearing requests and writes are never cached.
- Local SMTP and S3-compatible development emulators; internal S3 adapter with namespace/path/size checks and closed response streams. Callers must authenticate before choosing a workspace.
- Disposable database restore, worker restart and read-load diagnostics. SQL stays in memory; only the newly created UUID restore schema is removed.

## Verification

| Check | Evidence |
|---|---|
| API tests | 20 passed; approximately 88% unit/service coverage |
| Lint / TypeScript / build | passed |
| Live MySQL/Redis/Celery | retries, failure queue, concurrency, limiter, vault and session checks passed |
| Errors and SMTP | safe error visible to staff; alert delivered to local catcher |
| S3 emulator | round-trip and separate workspace prefixes passed |
| Restore | encrypted fixture token decrypted; restored queued work executed once |
| Worker restart | queued work survived and succeeded once |
| Read load | 10,000 job records; 100 requests, ten concurrent clients; p95 **104 ms** initially and **127.95 ms** in the consolidated run, target 300 ms |
| Browser | staff pagination, real nonstaff 403, six states, languages, themes, motion, mobile/tablet and revocation passed |
| Accessibility | axe WCAG A/AA scans passed on access/dashboard; keyboard/dialog checks passed; not full certification |
| Offline | real local HTTP install/control, reload/preview and private-data exclusion passed |

`scripts/exit_phase0.py` passed all **11 local checks** in a consolidated run. It records live-provider and human-review verification as unverified rather than treating those checks as production certification. Logs remain in ignored artifacts. CI runs the individual checks too.

## Remaining whole-feature gates

**PL-3:** native-language review and broader manual device/accessibility coverage. Automated scans cover the tested screens only.

**PL-5:** live managed-key deployment, actual provider refresh/revocation and verified provider-specific permission grants. The environment vault/key interface is tested; unknown providers stay disabled.

**PL-7:** actual connector quotas, provider idempotency and ambiguous external-outcome reconciliation. Generic local queue/recovery is tested; no external sending job is enabled.

**PL-8:** real model usage ingestion and owner-approved external alert destination. The metering primitive and local delivery are tested; fixtures are not live bills.

Counts remain **0 full phases / 0 whole production features**, four in progress and 253 not started. P1 is not opened by relabelling local tests as production proof.

## Development limits

The selected MinIO image was unavailable; Moto's documented S3 server mode supplies the internal development emulator. Its state is ephemeral and must not hold customer assets. Production storage needs approved credentials/policies/backups.

Mail goes only to `local-operator@example.test` in the local catcher. No real customer/operator email was sent. The load result measures foundation job reads, not 100 real users or future post-publishing capacity.
