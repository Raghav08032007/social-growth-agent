# Phase 1 plan — prepared, execution gated

P0 whole-feature gates remain open as recorded in the completion-pass report. This plan does not mark P1 started or any integration approved. The user's authorization to continue is retained; do not ask for the same blanket permission again when those gates pass.

First vertical slice: email magic-link authentication through a real mail adapter, confirmed business profile, a versioned draft and explicit owner approval. Local mail is delivered only to the test catcher; production mail requires owner-approved sender/domain configuration. Google/phone authentication and social adapters are separate independently verified paths, not disguised mock success.

Before coding, refine ON-1/ON-2/ON-3/ON-7/ON-8 and PB-1/AG-3 acceptance criteria with the original feature guide. Magic links require random hashed single-use tokens, short expiry, atomic consumption, rate limits, account-enumeration-safe responses, approved redirect origins, session issuance/revocation and audit entries. Never expose operator provisioning as public signup.

Profiles are tenant-scoped and versioned, preserve field provenance/confidence, and require explicit confirmation. Caption writing needs an approved model, structured outputs, actual usage metering, budgets and reviewed en/ta/hi examples. A local writer fixture must stay test-only. Any content edit invalidates approval; publication requires the exact approved variant/version.

For actual Instagram/Facebook publishing, the owner must authorize appropriate accounts and developer access. Verify exact login route, professional account type, API version/scopes, app-review eligibility, media formats, token refresh/revoke and reconciliation before enabling each action. Unknown capabilities remain disabled. A manual export/reminder route is a legitimate fallback, not a live publish claim.

External requirements: native-language review, approved business/provider accounts, sender/domain and usage budget decisions, and sandbox test assets owned by the operator. Do not request secrets in chat. Keep fixture, provider sandbox and live outcomes distinct in the report.
