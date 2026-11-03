# Recurring billing, purchase orders and the refreshed showcase

## What changed

The overview now prioritizes meaning-labelled monthly financial activity, evidence coverage, tracked balances and review tasks. The full import explorer is in **Source data & insights**, not duplicated on the home page. Revenue, reported sales, expenditure, cash movements and commitments remain separate. Charts use full authorized database aggregates, preserve source dates and expose exact figures. Missing periods are not zero-filled; the latest month can be incomplete. Balance amounts are not profit.

### Recurring invoices

Create a fixed-charge monthly, quarterly or yearly schedule for an existing customer. Set start/end dates, tax amount, discount and payment terms. **Generate due drafts** prepares up to 120 occurrences through today, without posting revenue. Repeated generation is safe. The original day is retained across shorter months (January 31 → February 28/29 → March 31).

Review a draft, then **Confirm & issue invoice**. Issuance creates a verified invoice and a tracked unpaid receivable in one transaction, with the schedule, draft and issue date retained as provenance. Repeating issuance returns the existing invoice. Skip unwanted drafts or pause future generation. Generated drafts retain their original terms. Change charges by pausing the old schedule and creating a new one.

**Boundary:** this release uses an explicit due-draft run during billing review. There is no unattended background scheduler, automatic email, payment collection, proration, credit-note workflow or statutory tax calculation. Issuing confirms a new unpaid charge; do not issue charges already imported through another source. An issued invoice is immutable under the existing tracked-invoice rule.

### Purchase orders

Create an order for an existing vendor with custom or catalogue-linked lines, quantities, unit prices and explicit tax amounts. Line totals use Decimal with half-up cent rounding. Save as draft, review and approve, or cancel with retained history. Approval records a commitment only.

When a matching supplier invoice is received, **Record matching bill** requires its reference/date, reviewed opening-paid amount and explicit full-order match confirmation. The resulting bill appears in Payables and supports the existing partial-payment and audited-void workflows. Conversion is atomic and retry-safe; it cannot post twice or turn an order into a customer expense.

**Boundary:** full-order conversion only; no partial delivery/billing, inventory movement, automatic vendor transmission, currency conversion or general-ledger posting. Wrong draft orders can be cancelled and recreated. Billed orders cannot be cancelled; a future audited bill-adjustment workflow is needed for monetary corrections.

## Refreshed demonstrations

### ProfitLens Studio — Synthetic demo

`scripts/datasets/showcase_2026.py` prepares eight explicitly fictional customers, 36 invoices and 72 attributed expenses for May–October 2026, four reviewed contract PDFs, two recurring schedules, three vendors/items/purchase orders, a converted bill, partial customer/vendor payments and one issued November recurring invoice. The second recurring occurrence remains a draft for the panel demonstration. Selected cost reviews are attested against current hashes; one customer intentionally remains unverified. There are deliberate pricing and cost-change examples.

All business writes use authenticated application APIs. CSVs use preview/confirm. Re-running the fixture does not duplicate records. `demo-files/showcase-2026/new-import-invoices.csv` is deliberately unimported for a drag-and-drop demonstration.

### Real data — DWP spending, 2026

Publisher: UK Department for Work and Pensions. Original monthly releases were published on 30 October 2026:

- [July 2026](https://www.gov.uk/government/publications/dwp-spending-over-25000-july-2026): 11,947 original rows.
- [August 2026](https://www.gov.uk/government/publications/dwp-spending-over-25000-august-2026): 8,501 original rows.
- [September 2026](https://www.gov.uk/government/publications/dwp-spending-over-25000-september-2026): 9,750 original rows.

Licence: [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/), as stated on the publisher pages. Contains public sector information licensed under the OGL v3.0. Downloaded 3 November 2026. Unchanged originals, SHA-256 manifest and prepared files are private under `data/private/dwp-2026`. Reproduce with `python scripts/datasets/dwp_refresh.py`; each download is bounded to 3 MB.

Selection: first 200 rows of each release in source order (600 total), **not** a representative estimate or total departmental spend. The separate `new-import.csv` contains the next 20 rows per release for a demonstration import. Original payment numbers are retained but are not assumed unique invoices or links to contracts.

| Source | Target | Transformation |
| --- | --- | --- |
| Transparency Invoice Amount | Amount → expenditure amount | Preserve original; remove GBP symbol/thousands separators in additional normalized field |
| Invoice Paid Date | Date → occurred_on | Preserve original; DMY to ISO; this remains a paid date, not an invoice issue date |
| Supplier Name | counterparty | Exact source name; no invented customer/vendor relationship |
| Invoice Account Description | description | Unchanged |
| Other original columns | retained raw fields | No silent discard |
| Original file URL + row | raw provenance | Added explicit source references |

Original encoding is Windows-1252; prepared CSV is UTF-8. All original columns remain alongside normalized values. Independently calculated subset totals: July GBP 151,208,875.66; August GBP 175,331,555.00; September GBP 213,141,583.00; combined GBP 539,682,013.66. These are totals of the selected published expenditure rows, not sales, customer profitability or newly outstanding bills. No linked contracts, purchase orders, customer revenue or delivery costs are supplied. The real workspace deliberately does not invent those features' input data.

Earlier demo workspaces are preserved and labelled `Archive - …`, recoverable through **Show earlier demos**. Personal uploads and existing records are not deleted. Current synthetic and real data never share an organization.

## Architecture, verification and deployment

Four additive tables: `recurring_schedules`, `recurring_drafts`, `purchase_orders`, `purchase_order_lines`. Composite organization keys protect relationships; financial values use NUMERIC/Decimal. Workspace transaction locks serialize generation, issue and conversion. Admin/finance roles only; analysts cannot inspect these organization-wide subledgers. Audit events retain transitions. Frozen Alembic revision: `20261103_planning`.

Run:

```text
python -m alembic upgrade head
python -m alembic check
python -m pytest -q
cd apps/web
npm run lint
npm run typecheck
npm run build
npm run test:e2e
```

Use isolated `_test` PostgreSQL databases for tests. The real-data test is explicitly skipped if the private downloaded dataset is absent; it is not replaced by synthetic evidence. The synthetic fixture is exercised through the same authenticated API sequence used for publication.

Final local backend run: **202 passed in 19.50 seconds**, including the synthetic showcase and actual real-data import tests. The first browser run passed 23/27; four stale dashboard assertions were corrected, then all 15 affected presentation/import/workspace scenarios passed. The new recurring/PO workflow, mobile layout and automated accessibility checks passed. Production build, fresh schema comparison and empty downgrade/re-upgrade passed. Hosted publication verification will be appended after execution; these local results do not claim a live deployment.

Rollback: redeploy the previous application release and retain the additive tables. The migration refuses to drop populated planning tables. A verified private backup must precede production migration; backup restoration has not been tested in production. No new paid infrastructure or external AI calls are required.

## Public workflow references

The behavior was informed by official [Zoho recurring-invoice documentation](https://www.zoho.com/in/books/help/recurring-invoice/) and [purchase-order documentation](https://www.zoho.com/in/books/help/purchase-order/). ProfitLens implements its own bounded workflows and original interface; it does not claim Zoho feature parity, certified accounting compliance or a measured cost advantage.

## Hosted release verified - 3 November 2026

PR #2 merged as `3061e168fffb30566fc6446f2df3f53ed2511217`. GitHub application checks passed in run 41651666085. Both Vercel Production deployments completed successfully:

- Web: `Buw52tSPfx3BF8f3PvKXfx11M8ML`
- API: `H32ocxWoXALH1FUEnPLJRP97HHqR`
- Live application: https://profitlens-six-psi.vercel.app/

The failed frontend Preview was caused by absent `API_INTERNAL_URL` in Preview. Production already had the required setting and built successfully. Production database/storage secrets were not copied into Preview. A fully connected isolated preview environment remains unconfigured.

Authenticated hosted publication verified 8 synthetic customers, 37 invoices, 72 expenses and 4 reviewed contracts. Recurring schedules, invoice issuance, three purchase orders, bill conversion and partial payments were populated through the existing APIs. Tracked receivables were INR 160776.00 and payables INR 5000.00 at publication.

The separate real workspace contains 600 DWP expenditure observations totaling GBP 539682013.66. Monthly totals matched the source subset, confirmation was repeated safely, the downloaded source matched uploaded bytes, and unsupported profit remained unavailable. Unauthorized workspace access was rejected. Four earlier demo workspace labels were reversibly archived; business records were preserved.

Hosted browser checks passed for login, default synthetic workspace selection, loaded recurring schedules/drafts, loaded purchase orders and the real workspace's 600 observations. Four screenshots were captured and visually inspected privately. The first smoke attempt filled the login form before intro readiness; waiting for the existing `data-intro-ready` signal corrected the test. No application authentication changes were needed. No AI provider calls were made in this release verification.

The earlier local-only PDF remains a dated pre-release snapshot and is not published in the current GitHub tree.
