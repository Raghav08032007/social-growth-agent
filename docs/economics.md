# Financial model and assumptions

Planning scenarios in INR; no current vendor price quote or profitability promise. The attachment's model names, token prices, payment rates, taxes, adoption statistics and exchange rate are not carried forward as verified facts. Taxes, founder compensation, acquisition and staff must be modeled separately.

The original proposed mix (50% at ₹499, 40% at ₹1,499, 10% at ₹4,999) gives weighted monthly revenue **₹1,349/account**. This arithmetic is correct; the mix is unvalidated. A pilot should test a simpler package before assuming that mix.

## Base illustrative scenario

Assume variable AI + messaging + storage ₹300/account/month; effective payment processing 3.5% of subscription revenue (hypothesis, not a quoted fee); infrastructure ₹10,000/month; support/tools ₹5,000/month. Revenue excludes tax and commerce commissions. Usage caps determine actual economics.

| Paying accounts | Revenue | Usage | Payment assumption | Fixed infra + support | Contribution after listed costs |
|---|---:|---:|---:|---:|---:|
| 10 | ₹13,490 | ₹3,000 | ₹472 | ₹15,000 | **−₹4,982** |
| 100 | ₹134,900 | ₹30,000 | ₹4,721.50 | ₹15,000 | **₹85,178.50 (63.1%)** |
| 1,000* | ₹1,349,000 | ₹300,000 | ₹47,215 | ₹105,000 | **₹896,785 (66.5%)** |

*At 1,000 accounts, assume ₹45,000 infrastructure and ₹60,000 support/tools. This is an illustrative scale adjustment, not a capacity quote. These are contribution scenarios after listed costs, not audited gross/operating margin.

At ₹1,349 ARPA, ₹300 usage and 3.5% payment cost, contribution before fixed costs is ₹1,001.785/account. Covering ₹15,000 takes **15 paying accounts** arithmetically, excluding labor, acquisition and taxes. At ₹150 usage it is 14; at ₹600 usage it is 22. Any founder salary, churn or failed collections changes the threshold.

At ₹499 with ₹300 usage and the same fee assumption, only ₹181.535 remains before infrastructure/support; at ₹1,499, ₹1,146.535 remains. This is why a cheap unlimited plan is unsuitable. Pass-through messaging credits should be separated from subscription revenue and supplier costs consistently.

## Inputs to measure

Model calls/token counts per approved draft, drafts discarded, inbound-message volume, paid template sends, media seconds, storage/egress, payment success/refund rates, collection fees, support minutes, churn, customer acquisition cost and retained revenue. Budget scenario low/base/high usage at ₹150/₹300/₹600 initially, then replace with measurements. Do not claim 75% margin until real billing and cost data support it.

The source's local development line items sum to ₹2,300–₹21,000, not its stated ₹2,500–₹12,000. Treat that as internal arithmetic, not a recommendation to buy a specific coding plan. Get provider quotes and account-specific eligibility before committing. Use scripts/economics.py to reproduce the illustrative model.
