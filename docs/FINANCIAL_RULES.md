# Week 4: revenue, recorded costs and evidence quality

This document describes the unchanged `/finance` endpoint. The newer `/profitability` endpoint adds contribution, margin, cost attestations and discrepancy rules; see [Analysis guide](ANALYSIS_GUIDE.md). Week 4 statements below are historical scope, not the current feature limit.

## What is implemented

Open **Revenue & costs** in any authorized workspace. The server computes exact recorded amounts for each customer and selected billing month; each total expands to invoice/expense IDs, original CSV rows or manual provenance, and private contract evidence. Admin/finance see their organization's customers; analysts see only assigned customers. The browser does not calculate financial totals.

| Value | Rule |
| --- | --- |
| Net billed revenue | Sum of invoice `subtotal - discount - refund`. Subtotal is before discount and tax. |
| Excluded tax | Retained per invoice for inspection; excluded from revenue, never subtracted from an already net value again. |
| Payable invoice total | Validated as `subtotal - discount + tax - refund`. This is different from revenue. |
| Recorded attributed costs | Sum of validated expense `amount` for the same organization, customer and month. Inputs must already exclude tax; the app does not infer tax or its recoverability. |
| No invoices / no expenses | Corresponding value is `null` / **Unavailable**, never inferred zero. |
| Explicit zero input | Retained as `0.00`. Zero revenue adds a warning; margin is not calculated. |

Python Decimal and PostgreSQL NUMERIC preserve exact amounts. Inputs permit at most two decimal places and amounts below 10^12 per field. Arithmetic is summed before two-place output formatting (`ROUND_HALF_UP`); valid inputs already have two-place precision so no intermediate rounding changes them. JSON amounts are strings; the report formats those strings without JavaScript floating-point conversion.

The supported refund is a pre-tax invoice reduction in the same month. Prior-period credit notes, tax-inclusive refunds, negative net revenue, shared-cost allocation, currency conversion and automatic tax treatment remain unsupported. This is net **billed** revenue, not cash collected or statutory profit.

## Quality states and warnings

A present cost row does not prove all costs were supplied. Costs remain **completeness unverified**; there is no completeness declaration workflow yet. No final contribution, margin or pricing anomaly is claimed in Week 4.

- Missing invoice/expense rows: show unavailable amounts with `missing_invoices` / `missing_costs`.
- Invalid amounts, currency or record references: block the affected total, preserve a reason, and show **Needs correction**. Foreign keys and existing import/edit validation reject these cases before storage; the calculator also defensively validates its inputs.
- Duplicate stable ID with identical validated values: counted once and warned about. Conflicting values for the same ID block the affected total. Database keys and transactional import fingerprints already prevent persistent duplicates. Equal amounts under different IDs are legitimate independent rows and both count; this is not fuzzy duplicate detection.
- No reviewed same-currency contract covering the entire month: `unmatched_contract_period`. Contracts do not change the recorded invoice arithmetic.
- Unreviewed documents: excluded from coverage matching and visibly flagged.
- Partial-month or overlapping reviewed periods: warnings; no automatic proration or combining partial contracts. A complete match includes both the first and last calendar day, including leap-day months.

These are evidence-quality warnings, not economic anomaly findings. Contract pricing mismatch, unusual cost increases and margin declines are Week 5 work.

## API and calculation boundary

`GET /api/workspaces/{organization_id}/finance`

Optional query parameters:

| Parameter | Meaning |
| --- | --- |
| `billing_period` | Valid YYYY-MM; default is the latest invoice/expense month visible to the caller within the customer filter. |
| `customer_id` | Exact accessible customer; unauthorized or unknown returns 404. |
| `limit` | Customer page size, default 25, range 1–100. |
| `offset` | Nonnegative customer offset. |

Response includes `billing_period`, `currency`, `calculation_version` (`revenue-cost-v1`), `total_customers`, pagination and `items`. Each item includes nullable revenue/cost strings, status, completeness, warnings and detailed source lines. Empty workspaces have no default month; selecting a month explicitly shows missing evidence for their accessible customers. The screen labels how many customers are shown; it does not represent one page as a whole-workspace aggregate.

Amounts include **all** matching source records for the customer page, independent of the existing 200-row record-list preview. A maximum of 10,000 source rows per type/page is enforced: if exceeded, return 422 with a request to narrow the selection, never a partial total. Customer picker remains limited to the existing first 200 customers; report pagination covers all accessible customers.

Session and organization membership are resolved before retrieval. All record, contract and default-period queries apply the same customer authorization predicate. A shared workspace lock coordinates the read with existing write locks, avoiding a calculation assembled across simultaneous imports/edits. Calculations are recomputed on request; they are not stored as stale snapshots. Revoked assignments affect subsequent requests. Contract links use the existing authorized file endpoint; no private storage keys are exposed.

Other errors: 401 when signed out; 404 for inaccessible workspaces/customers; 422 for invalid months, pagination or excessive source rows. The UI hides stale results on request failure and offers Refresh.

## Demonstration and verification

Run `python -m profitlens.manage seed-presentation` from a configured repository root, then Refresh. Select September 2026 and the four `W4-` customers. [Expected amounts and steps](../data/week4/README.md). The original `DEMO3-` upload pack stays separate.

`tests/test_finance.py` contains independent golden arithmetic and defensive input tests. PostgreSQL/API cases in `tests/test_workspace.py` verify retries, authorization/revocation, more than 200 source rows, customer pagination and the no-partial-total guard. Browser cases in `apps/web/tests/finance.spec.ts` cover displayed amounts, source navigation, missing/zero states, month selection, mobile width and analyst restrictions. See [progress](ROADMAP.md) for actual run results.
