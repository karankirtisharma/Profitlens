# Week 4 synthetic financial examples

These fixtures are preloaded by `python -m profitlens.manage seed-presentation` (and fresh `seed-demo`). They use W4 IDs; the separate `demo-files/` upload pack is unchanged. Existing seed runs and edits remain idempotent.

In **Revenue & costs**, choose **September 2026** and one customer:

| Customer | Net billed revenue | Recorded attributed costs | Demonstration |
| --- | --- | --- | --- |
| W4-EXACT | INR 850.00 | INR 200.30 | 1000.50 minus 100.25 discount minus 50.25 refund; 90.00 tax excluded. Source rows remain inspectable. |
| W4-ZERO | INR 0.00 | INR 0.00 | Full supported refund and an explicit zero expense. Zero revenue is warned about. |
| W4-MISSING | INR 500.00 | Unavailable | Absent expenses never imply zero cost. |
| W4-COSTONLY | Unavailable | INR 40.00 | Cost-only month; no invoice is invented. |

All recorded costs remain completeness-unverified: even an explicit zero row is not a declaration that every cost was supplied. These customers have no reviewed contracts, so contract coverage warnings are expected. For reviewed/unreviewed PDF examples, use C001/C002 in the baseline seed. The financial view makes no contract-price comparison yet.

Alternatively import these CSVs manually in customer, invoice, expense order. Retry the invoice file and verify the report is unchanged. This pack is a small deterministic test scenario, not the complete evaluation dataset or real business data.
