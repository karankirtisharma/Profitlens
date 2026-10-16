# Adaptive real-data demonstration

> The later user-authorized source-first implementation supersedes the legacy-invoice hosted publication plan below. See [current release and actual demonstration](SOURCE_FIRST_RELEASE.md). Preparation figures remain useful; the hosted real UCI demo uses raw source observations and reviewed XLSX mapping.

## Scope

ProfitLens remains a minor-project prototype for investigating customer profitability. This change supports incomplete financial exports without inventing accounting inputs. It does not add an ERP, tax engine, general ledger, payment reconciliation, industry presets or automatic schema mapping.

Two invoice bases are explicit:

| Basis | Required information | Supported output |
|---|---|---|
| `verified` (existing default) | Customer, month, currency, subtotal, discount, tax, refund, total; exact identity must hold | Net billed revenue; contribution when attributed costs exist; provisional until cost completeness reviewed |
| `reported_sales` | Customer, month, currency, source sales amount in `total`; breakdown must be absent | Reported sales totals, monthly chart and customer ranking; never net revenue, receipts or profit |

For a customer/month containing any reported-sales invoices, net revenue and contribution are unavailable. The dashboard separately shows verified-breakdown revenue and reported sales. Missing expenses do not become zero. Contracts are optional; absent documents no longer create a false unmatched-period warning. Provided but unreviewed, expired or overlapping contracts still require review.

The dashboard endpoint aggregates all authorized records in PostgreSQL. Its counts/totals are not limited to the 200-row UI preview. The older record-count chart explicitly remains a preview. Absent expenses/contracts do not occupy empty inventory tiles; capability explanations remain visible. Source amounts retain Decimal arithmetic; chart widths alone use floating-point display values.

## Real source and licence

[Online Retail — UCI](https://archive.ics.uci.edu/dataset/352/online+retail), Daqing Chen, donated 5 November 2015; [DOI](https://doi.org/10.24432/C5BW33), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). UCI describes UK retailer transactions and unit prices in sterling, with original invoice and customer identifiers. It does not provide linked delivery costs, contracts or a tax breakdown. The source is a retail demonstration of the data handling, not validation with our intended B2B service users.

Downloaded 16 October 2026: [original ZIP](https://archive.ics.uci.edu/static/public/352/online%2Bretail.zip), 23,715,478 bytes; SHA-256 `f5385cbb54bbebf7196389109c6b0621faab0c304e3702548165e71c84aede8b`. Unchanged archive and manifest remain under `data/private/uci-online-retail/`, excluded from Git. The repository contains reproducible preparation/publishing scripts, not private data or credentials.

## Selection and transformations

Inspection found 541,909 lines, 4,372 known customer IDs and 25,900 invoice/cancellation IDs. Contrary to the catalogue's blanket missing-value label, the downloaded workbook has 135,080 missing CustomerID rows. There are 9,288 cancellation rows and 1,933 invoice groups with exact repeated lines. These are source inspection findings, not findings of fraud.

Select the first 12 sorted anonymous customer IDs having eligible positive invoices in at least four months and 40–140 lines over January–November 2011. Keep whole eligible invoices for that fixed cohort. Exclude missing customer IDs, cancellation/non-numeric invoice identifiers, nonpositive prices/quantities, conflicting customer/date identities and duplicate-line invoice groups. Do not remove a duplicate line and silently change an invoice. The resulting 1,084 lines form 67 invoices. Preload 64; reserve the final three for a new-import demonstration. This is a selected positive-sales cohort, not total company turnover, net sales after returns or a representative population.

| Original | Target / transformation |
|---|---|
| CustomerID | Exact `customer_id`; display `Customer ID (anonymous)`, no invented company names |
| InvoiceNo | Exact `invoice_id`; original retained in `source_invoice_no` |
| InvoiceDate | Excel serial → ISO timestamp, then `billing_period` YYYY-MM; no invented timezone |
| Quantity × UnitPrice | Sum original decimal strings per whole invoice; ROUND_HALF_UP once to GBP 0.01 |
| Currency | GBP, supported by UCI's sterling documentation |
| Tax, discount, refund, costs, contracts | Not supplied; no fabricated zero values or relationships |
| Original row numbers, raw sum, country, timestamp, URL | Preserved in `source_*` columns and stored original import provenance |
| Stock code, description, raw quantity and price | Preserved in private source-line sample and unchanged workbook; not flattened into invoice columns |

Binary workbook decimal artifacts remain in `source_raw_sales_sum`; rounding is explicit. Example original row 54,659: 48 × 0.42 = GBP 20.16; row 54,660: 24 × 0.42 = GBP 10.08. Complete invoice 540971 rounds to GBP 651.16. Initial 64-invoice sum: **GBP 24,634.70**. March selection: **GBP 3,859.07**; May: **GBP 1,146.51**. These describe the selection and do not explain causes.

## Import formats and source review

Existing strict CSV formats still work. Industry is optional for customers. A reported-sales CSV needs `invoice_id,customer_id,billing_period,currency,total,amount_basis`, with `amount_basis=reported_sales`. Optional `source_*` columns are retained verbatim. Other unknown columns are rejected explicitly; there is no hidden inference or silent discard. Preview displays the explicit basis and unknown breakdown before confirmation. Users can inspect original values in a record's source details. XLSX is converted by the source-specific preparation script; general XLSX upload and fuzzy column mapping remain out of scope.

## Teacher demonstration

1. Choose **Real Data - UCI Sales (GBP)**. Show the real-source badge, licence link and missing-information explanation.
2. Show reported sales, the 11-month chart and customer ranking. Explain that these are source-linked positive sales, not verified profit.
3. Open invoices and inspect invoice 540971's original row references, country and raw sum. Revenue/profit analysis shows unknown breakdown and missing costs honestly.
4. Open Imports → invoices. Browse `data/private/uci-online-retail/prepared/demo-new-imports.csv`, preview three records, then confirm. Refresh Overview; the full selection becomes 67 invoices and GBP 25,365.41. Reconfirming the same batch creates no duplicates.
5. Switch to **Northstar Services**, clearly labelled synthetic, to demonstrate reviewed contracts, cost completeness, contribution and discrepancy rules. Never describe those costs/contracts as belonging to UCI's retailer.

Preparation: `.venv\Scripts\python.exe scripts/datasets/uci_inspect.py` after downloading the original to the documented path. Publication: `.venv\Scripts\python.exe scripts/datasets/uci_hosted.py` after migration and API deployment, using the existing private cloud-admin configuration. The publisher never sends these files to AI. It provisions only a dedicated demo organization and owner membership; business records use normal login/preview/confirm APIs. It refuses to silently restore a revoked membership or overwrite conflicting data.

## Migration, deployment and rollback

Alembic revision `20261016_reported_sales` adds an invoice-basis column defaulting existing records to verified and allows NULL breakdown only for reported sales. A database CHECK enforces both alternatives. Apply `alembic upgrade head` to the configured database before the new API deployment; no existing financial values are rewritten. Do not auto-run migrations during requests. Existing Vercel frontend/API projects continue using their Production-only secrets and private storage.

Rollback: keep this compatible schema and redeploy the last verified UI/API only before reported-sales data is introduced. Once reported records exist, an old API is not compatible; prefer a forward fix, or explicitly export/remove those demo records before reverting. Downgrade deliberately refuses while reported-sales rows exist rather than filling unknown values with zero. Do not reset production or delete other workspaces.

## Verification

Backend: 146 tests passed after updating the expected no-contract behavior and correcting a new test's HTTP Created expectation. Frontend TypeScript, ESLint and isolated production build passed. New browser coverage exercises reported-sales upload, preview, confirmation, adaptive overview, source inspection and unknown tax fields. Existing suites cover financial calculations, permissions, private PDFs, retry handling, navigation, accessibility and responsive layouts. Final browser and hosted publication results are recorded below after execution.

Limitations: no complete genuine linked sales/cost/contract dataset was verified; this release makes incomplete real data useful without manufacturing completeness. No additional industry features, unallocated-cost allocation engine or automated mapping profiles were introduced. Real-data AI requests were not used in preparation or publication. Evidence-grounded chatbot metrics support reported sales separately from profit; broader live conversational evaluation is not claimed.
