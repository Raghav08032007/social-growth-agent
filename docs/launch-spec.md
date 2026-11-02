# Launch workflow contracts

These are production acceptance targets. The local demo covers only basic state and ledger behavior.

| Workflow | Required behavior | Failure and recovery | Completion evidence |
|---|---|---|---|
| Connect account | OAuth state/PKCE as supported, minimal scopes, encrypted token, capability check | denial, expired/revoked token, wrong account type → reconnect/manual route | provider sandbox grant, refresh and disconnect logs |
| Create draft | confirmed business facts, language selection, three structured variants, cost estimate | missing context → ask; schema/model failure → retry or manual editor | reviewed multilingual evals and metering |
| Approve | authorized reviewer approves exact content version | edit/reschedule races invalidate stale approval | version-conflict and negative permission tests |
| Publish | queued variant with idempotency reference, media preflight, reconciled provider ID | timeout → unknown then reconcile; never blindly duplicate | actual provider test post, calendar state, retry evidence |
| Capture lead | eligible inbound event maps to platform conversation and source post where known | duplicate event no duplicate lead; unverified identity stays separate | signed fixtures + live test reply |
| Reply | permitted message category, consent, send window and quota at send time | opt-out, warning, low confidence → pause/handoff | prohibited sends blocked and auditable |
| Record sale | verified provider payment reference or explicitly manual owner entry | unmatched events stay unmatched; currency mismatch rejected | signed test payment and ledger comparison |
| Refund | negative entry references original settlement; repeated event has no extra effect | partial refunds sum to at most settled value; event ordering reconciled | replay/out-of-order/chargeback fixtures |
| Report | show recorded gross/refunds/net, attribution source, unknowns and timestamps | insufficient data → plain explanation, no invented chart | totals reconcile to ledger and exported report |
| Data rights | authenticated export, disconnect/revoke, deletion job and completion status | backup/ledger retention explained under reviewed policy | export isolation, deletion verification, restore policy |
| Upgrade | provider test checkout, entitlement from verified settlement, usage caps | renewal failure → grace policy then downgrade; webhook replay safe | billing sandbox lifecycle and reconciliation |

## Attribution rule v1 (proposed)

Use a deterministic post/campaign reference stored with checkout/order creation. If a verified order has that reference, mark provider linked. If only a coupon is available, show coupon matched. Use a configurable 7-day last eligible click window for click-based fallback, display the rule and label it inferred; validate the chosen window in pilot interviews. Owner-entered sales stay manual. Do not infer identity from a matching display name. Do not credit untracked UPI transfers to a post. Separate attribution association from incremental lift.

Represent money as integer paise and ISO currency. Store order ID, payment ID, event ID, source, timestamp and reconciliation status. Do not sum different currencies without an explicit conversion record. The demo has INR-only full refunds; partial refunds and real webhooks are later production work.

## Proposed route families

`/v1/workspaces`, `/connections`, `/profiles`, `/posts`, `/approvals`, `/publish-attempts`, `/conversations`, `/leads`, `/orders`, `/payments`, `/refunds`, `/reports`, `/usage`, `/data-requests`, `/webhooks/{provider}`. OpenAPI must define auth, scope, pagination, version conflicts, idempotency and a common error envelope. Never expose provider secrets to the frontend.

## Roles

Owner manages workspace, billing, connections and deletion. Manager oversees content and leads. Creator edits drafts. Approver signs exact versions. Analyst reads redacted metrics. Client reviewer accesses only a signed limited review resource. Staff must not inherit tenant access merely from a UI flag. Every API and job enforces the relevant intersection of membership, scope and action policy.
