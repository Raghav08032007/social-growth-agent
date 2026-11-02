# Feature guide — proposed synthesis

The authoritative inventory is [features.csv](features.csv): **257 unique original IDs**, every feature marked planned. The original detailed Feature Guide was not supplied; this document defines delivery structure without claiming to recover it.

## Priorities

| Tier | Features to implement | Reason |
|---|---|---|
| Pilot foundation | tenant auth, roles, data rights, audit, queue, vault, costs | required before external actions |
| Pilot value | confirmed profile; caption variants in en/ta/hi; version approval; one publishing connector + manual fallback | reach an approved useful post quickly |
| Pilot revenue | source-tagged leads; tracked order reference; manual/provider sale labels; full refunds; dashboard | demonstrate the social-to-booking job |
| Launch expansion | rest of P0–4: billing, reports, storefront, WhatsApp voice flow, YouTube, caps | add after pilot usability and provider approval |
| Retention expansion | P5–7: engagement, media, intelligence and specialized assistants | selected by observed demand/cost |
| Agency expansion | P8: role matrix, client portal/review, reporting, API | paying agency demand |
| New businesses | P9–10: creator marketplace, memberships, apps, autonomy | separate commercial and provider gates |

No item becomes production complete because a related demo button exists.

## Feature families

| Prefix | Scope | Primary architecture module |
|---|---|---|
| ON | onboarding and connections | identity/profiles/connections |
| NI | niche knowledge and localization | business/playbooks |
| CS | content creation/media | content/assets/jobs |
| PB | publishing | publishing/adapters |
| AG | assistants and controls | agents/policy/usage |
| IN | inbox and lead workflows | inbox/leads |
| AT | analytics and attribution | reporting/attribution |
| GI | growth intelligence | intelligence/snapshots |
| MO | monetization and creator earning | commerce |
| PL | platform/foundation | identity/operations/billing |
| PR | product risk and usability | policy/consent/experience |
| NV | new differentiators | cross-module workflows |
| TW | teamwork and agencies | approvals/workspaces |
| MK | marketplace | campaigns/discovery |
| BC | brand campaigns | campaigns/rights |
| PX | competitor-parity extensions | assigned per individual issue |

## Definition required for every implementation issue

Include original ID and phase, user/problem, explicit non-goals, role, data ownership, state machine, API schema, scheduled jobs, provider capability evidence, UI states, translation scope, cost cap, accessibility, migration/rollback, acceptance test, error recovery and runbook. Distinguish fixtures, provider sandbox and production evidence. Use the launch workflow contracts for cross-cutting behavior.

The names in the CSV are not enough to implement all 257 features safely. Each issue begins as a specification task. Do not mass-generate identical “done” tests or manufacture detailed behavior for unspecified features. Record decisions and link them from the issue.

## Candidate additions to the existing catalogue

The following are proposed requirements/extensions, not silently added to the original 257 count. Some deepen existing IDs rather than create separate product features.

| Extension | Related IDs | Acceptance target |
|---|---|---|
| Connector capability registry | PB-2, NV-18 | disable unsupported format/action with reason and manual path |
| Unknown-outcome reconciliation | PB-7, PL-7 | provider timeout cannot cause a blind duplicate publish |
| Attribution evidence drawer | NV-1, PR-10 | each sale shows source, confidence, rule and matching reference |
| Refund/chargeback reconciliation | NV-1 | negative entries preserve original settlement and total constraints |
| Unmatched transaction queue | AT-3, NV-1 | owner can resolve with explicit manual provenance |
| Verified contact linkage | IN-1, IN-3 | cross-platform merge requires verified relationship |
| Approval tied to version | AG-3, TW-2 | edited caption/media invalidates prior approval |
| Budget reservations | AG-5, PL-8 | simultaneous agent runs cannot overspend cap |
| Retention/deletion status center | NV-4, PL data rights | visible job state, connector revocation and backup retention explanation |
| Operational restore drill | PL-7/8 | restored database/queue reconciles jobs without duplicate effects |

These are more valuable early than adding another network or a second marketplace. Scope and IDs are finalized during issue refinement.
