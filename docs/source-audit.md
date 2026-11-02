# Master-plan source audit

Audited 2 November 2026. Source: the user's pasted **Social Growth Agent: Master Build Plan**, dated 1 November 2026. This audit checks internal consistency and specification coverage; it does not independently validate vendor pricing, platform policies, laws, or market statistics.

## Feature reconciliation

The phase scope lists contain **257 feature IDs, all unique**. The reported phase totals are correct:

| Phase | Scope | Extracted IDs |
|---|---|---:|
| 0 | Foundation | 4 |
| 1 | Create and publish | 34 |
| 2 | Leads and inbox | 13 |
| 3 | Money loop | 21 |
| 4 | Launch ready | 10 |
| 5 | Engagement | 36 |
| 6 | Growth tools | 37 |
| 7 | Agents and creator tools | 20 |
| 8 | Teams and agencies | 23 |
| 9 | Marketplace | 29 |
| 10 | Ecosystem | 30 |
| Total | | **257** |

Phases 0–4 contain **82** features. No duplicate assignment was found. `features.csv` preserves each original phase assignment and feature ID; every status is `planned`, because the source establishes intent, not implemented behavior. One ID can contain multiple products or connectors, so 257 is a catalogue count, not an implementation effort measure.

## Missing specification inputs

The source repeatedly references `docs/BLUEPRINT.md` and `docs/FEATURE_GUIDE.md`, but their complete standalone contents were not included. Phase prompts provide names, selected build notes, and exit tests, rather than full behavior for all 257 features. Any replacement blueprint or feature guide must be labeled a new synthesis. Do not represent it as a recovered original.

Each feature still needs a user story, states, permission matrix, data contract, provider capability evidence, acceptance criteria, failure behavior, and delivery estimate. Group-level exit tests do not prove every feature in a group. Explicitly distinguish fixture tests, provider sandbox tests, and production-connected verification.

## Internal corrections and assumptions

- **Local monthly cost:** the stated coding-agent range (Rs 1,800–18,000) plus test AI range (Rs 500–3,000) sums to **Rs 2,300–21,000**, rather than the stated Rs 2,500–12,000. The 3.5-month total must use a consistent scenario.
- **Per-user cost:** the detailed AI subtotal is approximately Rs 200 and messaging approximately Rs 100 before other items. The financial scenarios use only **Rs 150 per user for AI and messaging**. Those are different assumptions and must not support the same claimed margin without reconciliation.
- **Revenue arithmetic:** the proposed 50%/40%/10% plan mix produces Rs 1,349 average monthly revenue per account. The 10/100/1,000-account revenue figures are arithmetically consistent. The cost and margin projections remain hypothetical.
- **Margin terminology:** the scenario table mixes infrastructure, payment fees, support, and tools and excludes founder labor, acquisition, hires, and tax. Its percentage is not evidence of a measured gross margin. Define cost of revenue separately from operating expense before presenting gross or operating margins.
- **Breakeven:** “around ten paying accounts” depends on plan mix, consumption, support and omitted costs; it is a scenario result, not a dependable business threshold.
- **Timing:** 14 weeks for 82 features and 12–18 months for all features are unsupported estimates. Feature bundles include several connectors and enterprise products. Platform approval waits, test coverage, translations, media workflows and security work require separate effort and dependency estimates.
- **Sequencing:** Phase 1 requires working delete-my-data and Phase 4 adds comprehensive export/delete; define a minimum safe deletion flow early and extend it later. Story/carousel publishing appears in Phase 1 build notes and PX-5 in Phase 6; clarify the incremental behavior. “A second platform” in Phase 5 is ambiguous because Instagram and Facebook are both Phase 1 requirements. Treat it as an additional connector beyond those two.
- **Architecture:** a simple workspace middleware alone does not prove isolation. Queries, background jobs, object-storage access, exports, signed links, webhooks, caches and staff tools all require tenant-aware authorization.
- **Attribution:** tracked links, coupons and payment references establish recorded associations. They do not prove causal sales uplift or that all sales were attributable. Define attribution windows, multi-touch precedence, unmatched events, manual entries, refunds and chargebacks. Never credit arbitrary untracked UPI transfers as verified post revenue.
- **Identity matching:** merging WhatsApp and Instagram into one conversation requires verified identity linkage; a matching display name is insufficient.
- **Undo:** distinguish canceling a queued action from reversing a published post, delivered message or completed payment. Some actions are irreversible; a universal undo promise is inaccurate.
- **Messaging guardrails:** 70% of a provider limit and wording variation do not independently establish policy compliance. Use documented capability, consent, permitted use, message category and eligibility rules per connector. A single “24-hour window” must not be assumed to describe every network and message type.
- **Marketplace money handling:** provider-supported split payouts or holds must be verified for the precise account, jurisdiction and business model. Do not promise regulated escrow from a generic payment-link integration.
- **Language quality:** loading en/ta/hi strings is distinct from reviewed translations and evaluated mixed-language AI behavior. Assign native-language review and measurable acceptance thresholds.

## Claims requiring fresh primary-source verification

The attachment has no supporting URLs or research bibliography for the following claims. Treat them as **unverified source claims**, not current facts:

1. Indian SMB WhatsApp adoption (60%), entrepreneur social-media importance (83%), and projected influencer spending (Rs 4,500–5,000 crore).
2. Competitor prices, free tiers, customer complaints, willingness to pay, and claims about ReplyKaro or Zorcha.
3. Codex plan prices and typical developer spending; the claimed Claude model name and token prices; availability of named models.
4. Hosting, database, queue, object storage, WhatsApp provider, SMS, domain, developer-account and registration prices.
5. WhatsApp template rates, free-message conditions, taxes, provider markups and broadcast eligibility.
6. Razorpay subscription/transaction fees, UPI AutoPay availability, retry behavior, KYC, split payouts and hold capabilities.
7. Platform permission scopes, publishing formats, private replies, story automation, follow-status detection, account analytics, competitor-data availability and approved use.
8. Legal/tax requirements for the founder's business, GST invoices, data deletion and consent, DLT, calling restrictions and marketplace payout operations.

The Rs 90/USD conversion is explicitly a planning assumption, not an exchange-rate quote. The 6.8/10 idea score and 7.5/10 launch score are opinions. The 13 displayed category scores average approximately **6.77/10**, so the stated rounded 6.8 is consistent. None establishes product-market fit.

## Recommended evidence labels

Use `observed runtime`, `vendor documented`, `proposed design`, `estimate`, and `unknown` independently. Public website descriptions demonstrate advertised workflows; they do not establish hidden backend behavior or a tested end-to-end replica. Preserve the original source and link each revised requirement to its original ID.
