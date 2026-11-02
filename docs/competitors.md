# Competitor investigation and replication boundaries

Investigated 2 November 2026 with the reverse-engineer-anything skill and REA controlled browser scenarios. Each scenario launched installed Chrome with an empty temporary profile, navigated to the supplied public homepage, waited 1.2–1.5 seconds, and captured accessibility text/URL. Buffer also captured DOM. REA reported termination of its owned browser processes. No accounts, purchases, private APIs, or authenticated dashboards were exercised. A successful capture means page observation succeeded; it does not prove product workflows or backend correctness.

## Evidence index

| Target | REA Evidence ID | Scope |
|---|---|---|
| Buffer | ev_95d37a10b1347b3ae6d145f71dbb57edd291ed3429a529831dce76e925945eec | public homepage DOM/accessibility |
| Whop | ev_9d142f3a928ba6cdfb4295717d72dc7dc6d06fdf60beac3383cd4e1f27ff7f32 | public homepage accessibility |
| Hootsuite | ev_aaf85f306838f0cd0ac025a68e94a0457c08d9c51e8342e9eede9a218c05972f | public homepage accessibility |
| Sprout Social | ev_247e5b9c5e69a352557998f49e002bfaab08d2b213182cf98ab1857b62ff26dc | public homepage accessibility |
| Agorapulse | ev_e0996b1f90400590e4efc27ceb7a793185ab7b54df09dfe3df80136f909d0c21 | public homepage accessibility |

Raw JSON captures are retained locally in docs/evidence/ and ignored by Git/public archives. They contain third-party page material. The first REA calls were rejected by schema validation before execution; successful scenarios used the declared wait action. Some web-search snapshots differ from live REA text; current REA captures establish what was visible in that run. Marketing claims remain claims.

## Product lessons

**Whop — commerce infrastructure.** Its public page advertises payments, ads, communication, account compliance, programmatic business operations and embedded checkout. Proposed adoption: storefront → order → payment → access/booking → refund, affiliate references and later memberships. Cards, wallets, trading and financing introduce a separate product/business model and are excluded from our roadmap. We have not verified settlement, membership entitlements, disputes or payout flows. [Whop](https://whop.com/)

**Buffer — straightforward publishing workspace.** The page presents content ideas, multi-network publishing, community replies, insights, collaboration, link-in-bio and AI assistance. Proposed adoption: idea → variant → approval → queue → status → insights. Keep first-use navigation simple; postpone the long connector list. Network support on a marketing page does not establish identical formats or permissions across networks. [Buffer](https://buffer.com/)

**Hootsuite — connected social operations.** The page presents planning/publishing, inbox routing, analytics, trends/listening, competitor analysis and AI-assisted action. Proposed adoption: planned content plus customer-care tasks and explainable next actions. Listening requires a viable data source and separate cost gate; broad parity is later work. No authenticated inbox routing, analytics query or AI action was tested. [Hootsuite](https://www.hootsuite.com/)

**Sprout Social — teams, care and intelligence.** Its page presents publishing/collaboration, engagement, analytics, listening and influencer campaigns. Proposed adoption: role-based approvals, case handoff, branded reports and eventually brand–creator workflows. Enterprise governance and creator discovery are distinct releases. An integration logo does not prove availability of a particular API action or plan entitlement. [Sprout Social](https://sproutsocial.com/)

**Agorapulse — team workflow and business results.** REA captured its homepage successfully although the web fetch returned 403. It advertises AI-supported planning, engagement, listening and measurement. Its official glossary documents approvals, inbox collaboration, writing assistance and analytics/ROI integration. Proposed adoption: explicit inbox ownership, saved replies, review links and source-labelled revenue. ROI reporting is already a competitor capability, so our differentiation must be demonstrated through local workflows. [Agorapulse](https://www.agorapulse.com/), [official glossary](https://support.agorapulse.com/en/articles/13779845-the-agorapulse-glossary)

## Functional mapping

Rows below map proposed implementation, not certified product parity. Source IDs refer to retained catalogue entries.

| Family | Inspiration | Our catalogue | Delivery tier |
|---|---|---|---|
| Ideas, AI writing, brand voice | Buffer / four social suites | CS-1–5, NI-1–6, AG-1–5 | pilot subset; full P1 |
| Calendar, variants, approval, publishing | four social suites | PB-1–7, PX-1–5, TW-1–6 | P1/P6/P8 |
| Inbox, replies, contact records | four social suites | IN family, PR-1–4, PX-11–23 as scoped | P2/P5/P10 |
| Analytics, reports, ROI | four social suites | AT family, GI-1–5, NV-1, PX-25–29 | P3/P6/P9 |
| Listening and competitor intelligence | Hootsuite / Sprout / Agorapulse | GI-6–15, NV-18, NV-25 | P6/P10 with licensed access |
| Commerce and recurring products | Whop | MO family, PL-13, PX-39 | basic P3; full P7/P10 |
| Team/client governance | social suites | TW family, PL-11, PX-36–38 | P8/P10 |
| Creator campaigns | Sprout / commerce direction | MK/BC families, AG-13–14 | P9 |
| Regional language, UPI, WhatsApp routine | our proposed combination | NI-4, PL-2/21, NV-1/2, PX-23 | pilot/P3 with capability review |

## End-to-end replication checklist

For each product, acquire an authorized trial/test workspace before claiming parity. Record exact plan, role, network, screen, inputs, state transitions, output, error and recovery. Test signup/onboarding; create/edit/approval; schedule/reschedule/cancel; publish and reconcile; incoming interaction/assignment/reply; export/report; connect/revoke; billing/cancellation; delete/export. For Whop add checkout, entitlement, renewal, cancellation, refund, dispute and provider-supported payout. For enterprise suites add role denial, client boundaries and report delivery.

Each observed workflow must become an original implementation specification with an acceptance test and source link. Current coverage for authenticated journeys is **0 verified** across all five products. Public-page capability mapping is complete for this investigation; full replication remains unresolved. Proprietary server logic, algorithms, contract terms and data entitlements cannot be recovered from homepage text.
