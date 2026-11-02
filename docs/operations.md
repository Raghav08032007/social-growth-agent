# Operations and release runbook (proposed)

The local demo is not deployable infrastructure. Production operations below must be implemented and exercised before launch.

| Signal | First response | Recovery evidence |
|---|---|---|
| Publish outcome unknown | pause duplicate attempts; query provider external ID/status | one reconciled post, no duplicate |
| Token expired/revoked | disable outbound connector and notify owner to reconnect | minimal scopes and refreshed capability state |
| Quota/eligibility warning | pause relevant action class, inspect provider response | verified reset/review, manual path |
| Duplicate/out-of-order payment event | acknowledge safely, reconcile order/payment/refund | ledger matches provider net settlement |
| AI budget alert | block new reservations, preserve drafts, show usage | measured settled usage under cap |
| Queue age/dead letters | inspect error class, pause unsafe retries, assign owner | bounded safe replay and reconciliation |
| Data request failure | retain visible pending state, retry safe work, alert operator | export/delete completion and token revocation |
| Suspected tenant exposure | stop affected path, preserve redacted evidence, investigate | access fixed, impact assessed, response under reviewed policy |

## Minimum production dashboards

API latency/error by route; queue age, retry/dead-letter counts; publish success/unknown; webhook lag and dedupe; reconciliation mismatches; AI reserve/settle; workspace cost; consent blocks; token failures; database/storage capacity; deletion job age. Alerts need an accountable operator and a real response procedure.

## Backup and release

Set backup interval and recovery objectives from business tolerance, not a generic template. Encrypt backups, restrict keys, and perform a restore drill. Verify restored job/outbox state cannot repeat money or sends. Use schema expansion before application rollout, health checks and measured canary. Record provider API versions and migration compatibility. Never add customer secrets or raw personal conversations to CI fixtures.
