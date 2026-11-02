# Connector capability register

Status as of 2 November 2026: no live adapter implemented or account connected. Entries below are requirements to verify, not confirmed permissions. Public competitor support never substitutes for our own provider entitlement.

| Connector | Needed for | Verification before enabling | Fallback |
|---|---|---|---|
| Instagram | profile, publishing, comments, eligible private replies, insights | chosen login route, professional account type, exact scopes/app review, format/media constraints, limits, refresh/revoke and messaging eligibility | caption/media export and reminders |
| Facebook Pages | publishing, comments/inbox, insights | Page role, app review, format/action permission, token lifecycle | manual publish/link attach |
| WhatsApp | inbound messages, templates, voice input, commands | business onboarding, template category, consent, send eligibility, webhook signatures, provider charges | web approval and lead list |
| Razorpay | checkout/links, subscriptions, refunds | account eligibility/KYC, test payment, webhook secret, order reference, refunds and settlement reconciliation | manual sale explicitly labelled |
| YouTube | channel analytics, Shorts upload | consent/scopes, quota, verification, upload visibility and processing | import owner-exported metrics |
| Other social networks | future connectors | action-by-action API coverage, commercial rights and pricing | disabled until tested |
| Listening/competitors | public snapshots/trends | official/licensed data, permitted retention, coverage and per-workspace economics | own-account analytics |
| Model/speech/media | content/voice/clip generation | available model ID, schema quality, language eval, token/media cost, data retention | manual editor/upload |

Meta's published Instagram documentation identifies account-type and publishing limitations; support is not uniform across formats. Verify the current selected route rather than copying a permissions string from an old example. [Meta's Instagram collection](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api)

The direct Meta private-reply documentation fetch returned 429 in this investigation. Exact reply windows and message limits therefore remain a pre-implementation verification task. Do not generalize one 24-hour rule across Instagram private replies and WhatsApp categories. A 70% send-rate cap is a budget choice, not policy authorization.

Razorpay documents signature verification over webhook payloads, duplicate-event handling and event-order concerns. Validate the original request bytes, retain a safe event identifier, and reconcile provider payment/order identity before crediting money. Current documentation also lists webhook/tunnel restrictions, so the attachment's blanket ngrok assumption must be rechecked. [Razorpay webhook validation](https://razorpay.com/docs/webhooks/validate-test/)

## Required capability record

For every action store provider/API version, source URL, verification date, supported account types/regions, scopes, app-review status, media constraints, quota semantics, consent/eligibility checks, retry behavior, external idempotency support, sandbox evidence and fallback. Set capability state to unknown, verified sandbox, verified live, degraded or disabled. Recheck on token errors/provider changes and before adding a customer network.

No website automation is used as a production connector. REA browser observation is research only. Production integrations use supported APIs and licensed data.
