# Real-world financial formats and dataset strategy

15 October 2026 · research draft · no new dataset downloaded or imported in this phase. Sources and product evidence are indexed in the [market review](market-and-case-study-review.md). Dataset metadata below was inspected on publisher pages; unmeasured sizes and unavailable direct downloads are explicitly marked.

> **Scope update — COM-711:** this is a reference catalogue, not a requirement to implement every format or entity. Core: documented customer/invoice/attributed-expense CSVs and readable contract PDFs. Optional after core readiness: two reviewed CSV layouts OR XLSX with the same semantics. XML/JSON adapters, OCR, accounting APIs, cloud repositories, payments and allocation engines remain future work. The [active SRS](../requirements/SRS.md) controls scope.

## 1. Business records are not interchangeable

| Record family | Meaning and useful identifiers | Formats / interpretation risk | Proposed treatment |
|---|---|---|---|
| Customers, vendors, contacts | Customer buys; vendor supplies; contact is a person/communication record | CSV/API master data; one party may have both roles; name not a unique ID | Separate customer/vendor entities, optional explicitly reviewed party association; preserve external namespace |
| Employee / payroll summaries | Employee is not necessarily an application user; payroll expense is not a customer allocation | HR/time exports; highly sensitive rates/names | Defer payroll; use approved aggregate cost pools or pseudonymous time entries with restricted access |
| Agreements, amendments, schedules | Legal agreement, successive terms and service applicability | Text PDF plus manual review; effective date differs from recorded date | Immutable versions and term evidence; do not overwrite history |
| Sales invoices / lines | Obligation for supplied items/services; header and line totals may use different tax/discount bases | CSV/XLSX/API; repeated invoice number across rows can be line items, not duplicates | Group by verified source invoice identity; validate line/header reconciliation |
| Credit notes / refunds | Credit changes billed liability; refund moves cash or settles a credit | Distinct references; negative row alone is not enough to choose a type | Review transaction kind, prevent double subtraction |
| Payments / bank lines | Cash movement and settlement application | One payment to many invoices, partials, prepayments, fees | Separate cash record, allocations and bank-reconciliation link; no assumed income |
| Vendor bills / receipts / expenses | Bill establishes payable; receipt supports purchase; expense records cost recognition | PDF/API/spreadsheet; gross/net/recoverable tax vary | Separate supporting evidence from cost event; preserve tax basis and recognition policy |
| Timesheets / projects / departments | Operational dimensions supporting cost attribution | Time rate may be selling rate or internal cost rate | Optional modules; units/rate meaning and allocation basis required for calculation |
| Inventory / PO / delivery | Quantity and purchasing/fulfilment obligations | Unit prices, units, receipt quantities, return/revision state | Deferred optional adapters; no stock valuation inferred from invoices |

These distinctions are supported by the Xero schema, Oracle receipt applications, Zoho invoice/project fields and Peppol/OCDS structures (M03/M05/M09–11). The proposed treatment is ProfitLens design, not a claim that all publishers use the same model.

## 2. Current formats and optional/future support

| Format | Present implementation | Optional/future handling — not all required |
|---|---|---|
| CSV UTF-8 | Strict customers/invoices/expenses headers | Review delimiter/encoding, indexed duplicate headers, original strings and source row. Reject ambiguous decimals/dates; no silent coercion |
| XLSX | Not implemented; optional only after core | Read selected sheets and displayed/raw values, reject macros/encrypted input, do not evaluate formulas or external links; identify missing cached formula results; cap uncompressed size/cells |
| Text PDF | Contract page extraction only, manually reviewed terms | Retain page/text spans and typed extraction candidates. No claim that arbitrary PDF invoices are already supported |
| XML/JSON invoice | Not implemented | Later allowlisted schema adapters with namespace/version validation; disable XML external entities; retain full original document |
| Scanned PDF/OCR | Not implemented | Later isolated OCR, language/page/bounding-box provenance and human review; extraction confidence never proves a financial link |
| Accounting APIs | Not implemented | Later incremental read-only adapters: OAuth scopes, pagination, cursor/version, rate limits, retries and source tombstones |
| Drive / OneDrive | Not implemented | Later user-selected folder inventory, source file ID/version, permission rechecks, explicit copy/export rules; no automatic crawl of all accessible files |

CSV/XLSX normalizers must handle decimal separators only under a reviewed locale, preserve leading-zero IDs as strings and keep date-only values distinct from timestamps. `03/04/2026` is ambiguous until format is confirmed. A source month is not an issue date. A total with unknown tax basis cannot become tax-exclusive revenue by filling tax with zero. Signed bank withdrawals are not necessarily negative expenses.

## 3. Candidate datasets and reuse evidence

### D01 — Folkestone & Hythe District Council procurement-card spending

Publisher: FHDC. Periods: April, May, September and December 2025. Existing original downloads dated 15 October 2026; original file bytes and manifest already stored privately. [April download](https://www.folkestone-hythe.gov.uk/downloads/file/5928/procurement-data-april-2025), [May](https://www.folkestone-hythe.gov.uk/downloads/file/5992/procurement-data-may-2025), [September](https://www.folkestone-hythe.gov.uk/downloads/file/6185/procurement-data-september-2025), [December](https://www.folkestone-hythe.gov.uk/downloads/file/6332/procurement-data-december-2025). [Publisher reuse statement](https://www.folkestone-hythe.gov.uk/council-transparency/councils-publication-scheme); [OGL v3](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

Existing inspection: four files advertised as CSV contain text PDF; 142 transactions, with 141 positive/zero debits imported and one −539 credit excluded by current nonnegative schema. Fields include transaction date, supplier, description, service area and amount/tax information. Exact byte sizes/hashes are in the private manifest, not remeasured here. The separate [contract register](https://www.folkestone-hythe.gov.uk/downloads/file/6741/contract-register-24august2026) has no verified transaction link. Good for extraction, missing-data and signed-credit gaps; not sales or customer profit. See [existing preparation/attribution report](../REAL_DATA_DEMO.md). Existing technical grouping records must not be relabelled real customers.

Manifest inspected in this phase: April 187,287 bytes; May 187,359; September 188,234; December 186,846; contract-register PDF 907,043; saved publisher licence HTML 41,731. These are recorded download sizes, not fresh transfer measurements. The publisher's reuse statement was readable during this research; the National Archives licence URL returned HTTP 403 to the research reader, so its full text was not revalidated here.

### D02 — UCI Online Retail

Publisher: UCI / Daqing Chen; donated 5 November 2015; DOI 10.24432/C5BW33. [Dataset and download control](https://archive.ics.uci.edu/dataset/352/online+retail). Explicit CC BY 4.0. Publisher lists 541,909 records and a 22.6 MB XLSX. Fields: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice (sterling), CustomerID, Country; cancellation indicator documented. Research browser could not fetch the binary download; no new download attempted by shell.

Use a deterministic 100–2,000-row subset retaining whole invoices, after schema inspection. It supports real sales-line and customer references, not linked internal costs/contracts or an explicit tax breakdown. Publisher's missing-value metadata is not a substitute for inspecting the file. Do not assume absent tax means zero or transform cancellation codes into cash refunds without evidence.

### D03 — City of Portland OCDS procurement

Publisher: City of Portland; [publication page](https://www.portland.gov/business-opportunities/ocds/ocds-data-publication), [March 20, 2026 download folder](https://drive.google.com/drive/folders/1Y5zQaBMqLSHHFC67qDh_jtmG2F-cJ0dF?usp=sharing), [publication policy](https://www.portland.gov/business-opportunities/ocds/pdx-ocds-publication-policy), [OCP registry](https://data.open-contracting.org/en/publication/155). City explicitly states PDDL 1.0; keep original source links and attribution with any derived sample. Download folder content/individual file sizes were not exposed by the research reader; no binary downloaded.

Registry snapshot lists 10,243 contracts and 400,146 transactions; these are publisher/registry counts, not locally verified rows. JSON/CSV/Excel access is described. OCIDs connect procurement stages; contract implementation transactions can provide genuine procurement links. This is the best next candidate for bounded contract/spend-link evaluation, subject to record inspection. Registry quality warnings and publisher release notes require review. Neither source proves supplier internal cost, supplier profitability or original invoice-PDF availability. Full aggregate download may be too large; select a publisher-supported small export or defer until bounded extraction is possible.

### D04 — Atomic Common-Day Invoice Clearing

Publisher: Peplluis Esteva de la Rosa / Mendeley Data, v1, 23 August 2026. [Dataset/download page](https://data.mendeley.com/datasets/28rbmvwsm9/1), DOI 10.17632/28rbmvwsm9.1; CC BY 4.0 displayed. Named archive: `mendeley_annual_runner_inputs_anonymized.zip`; direct binary URL/byte size not exposed. Publisher describes 749,952 retained 2012–2023 invoice records plus 1,240 terminal records, pseudonymous debtor/creditor/invoice IDs, integer euro cents and dates.

Potential for reference/currency/date and network tests. Not evidence of customer-cost attribution, VAT detail, contract PDFs or cash settlement. Publisher cautions that exact dates/amounts/relations remain pseudonymized and governing data-use agreements matter; resolve that caveat before downloading/publishing a derivative. No transaction files inspected in this phase.

### D05 — Microsoft/obviEnce Customer Profitability

Publisher: Microsoft / obviEnce. [Sample page/downloads](https://learn.microsoft.com/en-us/power-bi/create-reports/sample-customer-profitability), [usage terms](https://learn.microsoft.com/en-us/power-bi/create-reports/sample-datasets#legal-guidelines-for-using-samples). PBIX/XLSX; exact size/rows not inspected. Publisher describes real anonymized customer revenue/cost data. Terms restrict the context of sharing to Power BI demonstration; this is **not an unrestricted reuse candidate for ProfitLens**. No download/import. Aggregated profitability is not original linked invoices/contracts.

### D06 — Existing ProfitLens synthetic benchmark

First-party generated fixture, not real-company evidence: `evaluation_demo.py`, `data/evaluation/` and `docs/evaluation-results-2026-10-15.json`. Saved counts: 20 customers, six months, 120 invoices, 115 expenses, 40 contract PDFs, 30 questions. Governed by repository rights, not an invented open-data licence. Suitable for deterministic expected answers and security negatives. Use the existing bounded benchmark and [focused test strategy](../testing/test-strategy.md); no new broad multi-industry benchmark is required. Do not mix it into a genuine-data workspace or present it as satisfying the genuine-data-only request.

## 4. Selection decision

Keep D01 as genuine expense ingestion evidence. D03 procurement links and D02 invoice lines remain optional later research; do not build adapters solely to fill every dashboard card. A complete real-company dataset remains an unresolved user objective, not a verified asset or a reason to fabricate links. No verified openly reusable dataset in this review contains the complete supplier-side chain of customer sales invoices, attributed delivery costs and applicable contract terms. Combining Portland contracts, UCI invoices and council costs does not create one company. D04 needs provenance/privacy review; D05 is on hold for reuse permission.

The latest phase permits recommending a labelled synthetic benchmark but does not authorize falsely filling the real dashboard. The earlier genuine-data-only requirement remains respected.

## 5. Safeguards for any later acquisition — not a required new ingestion platform

1. Create isolated dataset/workspace namespaces. Save publisher URL, exact resolved download URL, licence URL/version, access date, source period, content type, length, SHA-256 and terms snapshot. Stop for ambiguous rights.
2. Use bounded streaming downloads with domain allowlist, timeout and maximum bytes; reject redirects to private/local hosts. For D03, inspect folder inventory before choosing a file; do not guess a direct download ID. For D02, original XLSX is larger than the application's import cap: preprocessing must be offline and bounded, with unchanged original retained.
3. Inventory actual MIME/signature, sheets/pages, headers/types, rows, currencies, nulls, repeated source IDs and transaction totals. Separate missing identifiers from genuine duplicates.
4. Sample deterministically: sorted source IDs or seeded stratified selection; retain complete invoice/contract groups and all child lines required for checks. Record seed and selected IDs. Do not cherry-pick only successful cases.
5. Produce mapping ledger: source field → target field, raw value → normalized value, transform/version, assumption/reviewer, unknown fields, exclusions and reason. Never silently repair signs or infer customer from supplier name.
6. Preview through normal authenticated API. Confirm only valid reviewed records, preserve failures. Demonstrate repeated-file retry and changed-record conflict in the evaluation workspace.
7. Verify selected totals manually and independently; cite page/row for each expected result. Reconcile exclusions to source totals. Publish only permitted, non-sensitive samples and aggregate test evidence.

Proposed mapping examples: FHDC supplier → vendor candidate, not customer; UCI InvoiceNo → namespaced external invoice ID and StockCode → line item reference, not customer contract; OCDS `contracts[].implementation.transactions[]` → procurement spending observation linked by its actual parent contract, not a supplier sales/cost pair. These mappings are proposals pending record-level inspection and workflow support.

## 6. Source access limitations and next step

Some vendor pages are dynamic or exceed reader limits. The official Xero raw schema and Oracle 26B guide were readable; official indexed excerpts are explicitly marked in the market register. Dataset binary downloads and fresh imports were intentionally not performed in research-only scope. After review, use the listed publisher download controls, inspect the chosen small export, save its exact file URL/hash and evaluate it without external AI transmission. No successful new download, import or full-real-data demonstration is claimed.

## 7. Minor-project demonstration decision

Demonstrate the already linked synthetic benchmark as synthetic to cover calculations, discrepancy rules and evidence. Use the existing genuine expense workspace only for the fields and links the source actually provides. An empty revenue or unavailable margin is the correct outcome for spending-only records. A complete genuine dataset is still not verified; reducing product scope does not change that fact or authorize a new synthetic replacement.
