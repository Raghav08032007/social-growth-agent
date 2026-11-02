# Verification strategy

## Evidence levels

1. Unit/service fixtures: deterministic state, authorization and accounting logic.
2. HTTP transport fixtures: real request handler with controlled in-memory streams.
3. Browser integration: user actions through actual UI and API transport.
4. Provider sandbox: actual OAuth/test network/payment flow, signed events and external IDs.
5. Production canary: permitted small live action, reconciliation and rollback/recovery.

Passing a lower level does not establish a higher one. Competitor homepage REA captures are research evidence, not product test evidence.

## Current checks

Seven Python tests cover lifecycle/refund, duplicate financial requests, payload conflict/atomicity, invalid transitions/fields, tenant-scoped reads and related writes, immutable ledger/audit, HTTP JSON/origin handling and static path restrictions. Frontend syntax is checked with Node. The catalogue validator checks exact IDs, counts, phases and planned status. The delivery report records actual results and browser limitations.

## Production acceptance matrix

| Risk | Required verification |
|---|---|
| Tenant leak | every endpoint, job, export, storage URL, cache and staff path with two tenants |
| Duplicate publish | timeout after provider accepts; reconcile before retry |
| Stale approval | edit content/media then attempt scheduled publication |
| Duplicate money | same event, different delivery, changed payload/key, concurrent requests |
| Event ordering | refund before settlement; delayed capture; partial refunds; chargeback |
| Unsafe send | opted-out contact, closed eligibility window, removed scope, kill switch |
| Agent injection | malicious inbound content asks for secrets, foreign tenant, spend increase |
| Budget races | simultaneous actions reserve/settle without exceeding cap |
| Token lifecycle | expiration/revocation, wrong scope, rotation, old-key decrypt |
| Data rights | authentic export, delete all owned derivatives, revoke tokens, backup policy |
| Accessibility | keyboard, focus after updates, screen-reader status, contrast, 360 px reflow |
| Localization | native-speaker review; mixed-language examples; dates/currency |
| Operations | worker crash, Redis outage, database failover, restore and safe job replay |

Use pytest with actual MySQL/Redis containers for production integration tests, Vitest for substantial client logic, Playwright for critical journeys, and reviewed language evaluation examples. Do not write dozens of mirrored tests to inflate coverage. The source's 85% backend target is secondary to meaningful negative tests.

## Release report template

Feature ID; implementation status; version; test command/result; fixture vs sandbox vs live; external record references redacted; latency/cost measured; known failures; manual prerequisites; rollback plan. A feature cannot be marked complete while its required provider journey remains untested.
