# Delivery roadmap

All dates and effort ranges below are planning estimates, not commitments. Feature counts come from the supplied scope lists. A feature ID may bundle multiple independent workflows.

## Pilot sequence

| Milestone | Estimated focused engineering effort | Exit evidence |
|---|---:|---|
| Discovery and capability review | 1–2 weeks | 10 interviews, pilot commitments, connector capability register |
| P0 production foundation | 2–4 weeks | authenticated isolation, migrations, queue retry/dead-letter, vault/rotation, CI, backups |
| Profile → draft → approval → one publish route | 3–5 weeks | provider sandbox publish + independent status reconciliation; manual alternative |
| Leads → tracked sale → refund | 3–5 weeks | signed event replay, ledger reconciliation, explicit attribution labels |
| Pilot hardening and onboarding | 2–4 weeks | deletion/export, accessibility, spend limits, restore drill, five workspaces |

Total sequential effort is roughly **11–20 engineering weeks after discovery** for the thin pilot. Review queues and vendor access can add elapsed time. This does not deliver all 82 P0–P4 features. Re-estimate after two completed slices using observed throughput.

## Full retained roadmap

| Phase | Features | Intended outcome | Gate |
|---|---:|---|---|
| P0 Foundation | 4 | secure shell, vault, queue, admin costs | isolation, retries, encryption and cost alert evidence |
| P1 Create/publish | 34 | onboarding, multilingual draft, approval, publish | real test account publish; revoke/expiry/error paths |
| P2 Leads/inbox | 13 | safe comment/message capture and follow-up | duplicate replay, opt-out and policy-eligible reply checks |
| P3 Money loop | 21 | attribution, storefront, reports, WhatsApp commands | provider test payment and refund reconcile; voice approval test |
| P4 Launch ready | 10 | subscriptions, caps, data rights, billing | renewal recovery, export/delete, realistic load and restore test |
| P5 Engagement | 36 | extra networks, deeper inbox, reputation | one additional supported network; routing and complaint handling |
| P6 Growth tools | 37 | media, competitor snapshots, deeper metrics | licensed data, media accuracy, store-order matching |
| P7 Agents | 20 | specialized assistants, creator earning | adversarial scope/cap tests; offer-to-booking reconciliation |
| P8 Teams | 23 | client approvals, roles, API, white-label | agency demand; cross-client and signed-link isolation |
| P9 Marketplace | 29 | discovery, contracts, milestone payouts | proposed threshold 200 active creators/20 interested brands; provider payout approval |
| P10 Ecosystem | 30 | guarded missions, native apps, paid community | proven retention and support capacity; scoped third-party tools |

Do not estimate P5–P10 as a fixed 12–18 month promise before staffing and provider constraints are measured. Whop-style commerce, enterprise care/listening and marketplace liquidity each form a substantial product line.

## Dependencies and sequencing corrections

Data rights, consent, role enforcement, spend limits and observability start in P0/P1; P4 extends them. Phase 1 carousel/reel support must be distinguished from later format enhancements. P5's “second platform” means an additional network beyond Instagram/Facebook. A role matrix is needed before any shared workspace, even though agency features are P8. A production pilot cannot omit fundamental controls because their original ID is assigned later.

## Work management

One issue per feature, then implementation tasks per workflow: data/migration, permission, API, jobs, UI, failure paths, tests and runbook. Keep feature statuses planned / in progress / demo only / sandbox verified / production verified. Preserve tests and evidence links when moving status. A phase report must list partial and blocked features rather than rolling them into a green phase badge.

Cut scope when provider access or pilot value is uncertain. Add a new network only after its publishing, token refresh/revoke, error recovery and reconciliation tests pass. Open the marketplace only after both supply and demand are demonstrated.
