# Real-data and synthetic dashboard demos

Updated: 16 October 2026. The real FHDC workspace is now also available on the [hosted site](https://profitlens-six-psi.vercel.app) to the existing Karan administrator. Select **Real Data - FHDC Expenses (GBP)**. It is separate from Northstar's synthetic demo. The two original local development workspaces described below remain available locally; the focused synthetic companion was not newly copied to hosting.

The hosted UI labels this workspace **Real-world public data · GBP** and displays publisher attribution, the OGL v3.0 licence, technical-bucket limitations and the absence of verified invoice/contract/customer-cost links. Product screens use capability wording rather than development-week milestones.

## Open the demos

1. For the hosted real dataset, open <https://profitlens-six-psi.vercel.app> with your cloud demo account. For both original local packs, open <http://localhost:3000> with your local account when local servers are running.
2. Reload the page after provisioning so the Workspace selector fetches your new memberships.
3. Choose the appropriate workspace below. The top badge also distinguishes public data from synthetic data.

| Workspace selector name | Contents at preparation | Best use |
|---|---|---|
| **Real Data - FHDC Expenses (GBP)** | 141 real expenses, 2 technical grouping records, 0 invoices, 1 unreviewed reference PDF | Show public-data import, source rows, expense totals and honest missing-data states. |
| **Synthetic - Financial Demo (INR)** | 3 fictional customers, 6 invoices, 5 expenses, 3 reviewed synthetic contract PDFs | Show customer profitability, pricing mismatches, cost increases and margin declines. |

IDs are `demo-fhdc-real` and `demo-fhdc-synthetic`. Organization keys and currencies remain separate. The two “customers” in the real workspace are explicitly named technical buckets; they are **not real customers or inferred business relationships**.

## What the real data contains

Source: **Folkestone & Hythe District Council procurement-card data**, April, May, September and December 2025, downloaded 15 October 2026. The four files contain 142 transactions. Although advertised/saved as `.csv`, their actual contents are text PDFs; their original bytes were preserved and converted to genuine CSV for import.

Source downloads: [April](https://www.folkestone-hythe.gov.uk/downloads/file/5928/procurement-data-april-2025), [May](https://www.folkestone-hythe.gov.uk/downloads/file/5992/procurement-data-may-2025), [September](https://www.folkestone-hythe.gov.uk/downloads/file/6185/procurement-data-september-2025), [December](https://www.folkestone-hythe.gov.uk/downloads/file/6332/procurement-data-december-2025).

The separate [24 August 2026 contract register](https://www.folkestone-hythe.gov.uk/downloads/file/6741/contract-register-24august2026) is a 72-page reference document. It has **no verified link to these transactions**, remains unreviewed, and is attached only to `UNLINKED-PUBLIC-REGISTER`. Register values are not treated as reviewed monthly prices.

The publisher's [publication scheme](https://www.folkestone-hythe.gov.uk/council-transparency/councils-publication-scheme) explicitly identifies the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

**Attribution:** Contains public sector information licensed under the Open Government Licence v3.0. Source: Folkestone & Hythe District Council.

### Transformations and exclusions

- Source **Amount → expense amount**, retaining exact cents. Amount is already net of VAT; VAT is not deducted twice. Original VAT/Gross are retained in the audit log.
- Source **transaction date → calendar month**. Publication months can contain earlier transactions, so there are seven transaction months.
- **Description → category**. Supplier and service-area text remain in the audit trail, not a guessed customer/contract relationship.
- Source has no transaction ID: generated IDs encode the source publication, PDF page and transaction ordinal. Original URL, SHA-256 and row coordinates are preserved.
- **GBP is inferred** from UK council reporting; no ISO currency column or exchange-rate conversion exists.
- **One −£539 credit is excluded**, because negative expense amounts are unsupported. It is preserved in the exclusion log, not silently made positive.

The 141 imported debits total **£28,362.37**. The source net total including the excluded credit is **£27,823.37**. Neither number establishes customer profit. Missing invoices and cost allocation mean revenue/contribution/margin must remain unavailable. Do not attest these partial, unallocated expenses as complete customer costs.

## What to show the teacher

**Real workspace:** Open Expenses to show source IDs and the imported source-row information. Open Revenue & costs or Profitability & evidence, select `UNALLOCATED-PUBLIC-SPEND`, and choose **December 2025**. Its debit cost is **GBP 6,035.77**; revenue and contribution are unknown. Open Contracts to show the separate unreviewed register. Explain why no customer or contract linkage was invented.

**Synthetic workspace:** Open Profitability & evidence and choose **September 2026**:

| Customer | Revenue | Cost | Contribution | Margin | Demonstration |
|---|---:|---:|---:|---:|---|
| EVAL-01 | INR 1,200 | INR 400 | INR 800 | 66.67% | Invoice price differs from the reviewed INR 1,000 monthly contract. |
| EVAL-06 | INR 1,000 | INR 800 | INR 200 | 20.00% | Cost increased from INR 400 in August; margin fell from 60%. |
| EVAL-11 | INR 1,000 | Unknown | Unknown | Unknown | Missing costs remain unknown rather than zero. |

These cases come from the project's existing synthetic evaluation fixture. They are not council transactions. Existing AI configuration was not changed, but publishing and verification made **no external AI calls**. The source-import demo does not require the chatbot.

## Browse/drag-and-drop import files

All local dataset files are in:

```text
D:\Profitlens\data\private\real-world-fhdc-2025\prepared\
  real\                    # Already loaded; reuse to show duplicate-safe imports
  synthetic-companion\     # Already loaded; separate fictional baseline
  synthetic-new-import\    # EVAL-02, deliberately NOT preloaded
```

To demonstrate genuinely new imports, select **Synthetic - Financial Demo (INR)** → **Imports**, then use `synthetic-new-import`:

1. Record type **customers** → `customers.csv` → Preview → Confirm (1 new customer).
2. Record type **invoices** → `invoices.csv` → Preview → Confirm (2 new invoices).
3. Record type **expenses** → `expenses.csv` → Preview → Confirm (2 new expenses).
4. In Contracts, upload `EVAL-02-current.pdf` for EVAL-02. Read the PDF before reviewing terms. It describes INR 1,000 monthly, no monthly discount, 1 April–30 September 2026, page 1. Only attest the synthetic costs after checking these fixture rows.

Before that confirmation, baseline customer/invoice/expense counts are **3/6/5**. After all three CSV confirmations they become **4/8/7**. Repeating an unchanged file must not duplicate its records. The browser verification left a **ready preview** for the new customer but deliberately did not confirm it, so the first live import is yours.

For real data, re-uploading `real/expenses.csv` demonstrates retry/duplicate handling; it is already fully loaded. Do not rename IDs to manufacture new purchases or import this GBP file into the INR workspace. The excluded refund is an unsupported input example, not a valid positive-expense upload.

## Evidence and reproducibility

### Hosted publication — 16 October 2026

Explicit publisher: `scripts/datasets/fhdc_hosted.py --publish-hosted-demo`, run from the repository root with `PYTHONPATH=apps/api` and the Git-ignored `.env.cloud-admin`. This is a one-off administrative operation, never a build/startup hook. It validates original SHA-256 hashes and prepared totals, signs in normally, provisions only the dedicated GBP organization and its existing owner's membership, then uses HTTP preview/confirm and PDF upload. It refuses conflicting workspace metadata or changed membership and does not bypass login lockouts. Re-running confirmation is duplicate-safe. Credentials and original data remain Git-ignored.

Verified through the hosted application: 2 technical buckets, 141 expenses, no invoices; total GBP 28,362.37; December debit cost GBP 6,035.77; contribution and margin remain null; the uploaded original register remains unreviewed and downloads with its original hash. Repeated import confirmations did not duplicate rows. Anonymous access returned 401 and an unrelated synthetic invoice ID returned 404. A fingerprint of business rows and memberships outside the new workspace was unchanged. No AI provider calls were made. The private report is `data/private/real-world-fhdc-2025/hosted-publication.json`.

The existing local prepared files can also be selected in the hosted Imports screen. Re-uploading the real pack demonstrates duplicate protection; the dataset is already loaded. Do not import synthetic records into the real workspace.

Local `data/private/real-world-fhdc-2025/` contains:

- `DATASET_EVALUATION_REPORT.md`: source selection, mapping, gaps and earlier isolated-test results.
- `manifest.json`, `originals/`, `transformations.jsonl`, `excluded-records.json`: unchanged downloads and complete transformation audit.
- `dashboard-publication.json`: actual dashboard publication counts and checks that existing workspaces were unchanged.
- `dashboard-browser-results.json` and `previews/dashboard-*.png`: browser verification and screenshots.
- `evaluation-results.json`: earlier **80 passed / 0 failed** checks in disposable `profitlens_test`. Those tests are distinct from this dashboard publication.

The new workspaces are in the normal local **profitlens** development database; the earlier `qa-fhdc-*` workspaces remain confined to **profitlens_test**. Existing account passwords and prior workspace data were preserved. A dedicated importer identity has access only to these two new workspaces; its randomly generated credentials are private and Git-ignored. The usual Karan account has admin membership in both.

If restoring this setup on the same local development configuration:

```powershell
Set-Location D:\Profitlens
.\.venv\Scripts\python.exe scripts\datasets\fhdc_prepare.py
# Start the normal API using dev.cmd, then explicitly publish:
.\.venv\Scripts\python.exe scripts\datasets\fhdc_dashboard.py --publish-local-demo
```

The publisher uses ordinary HTTP password login, preview/confirm and PDF review endpoints. Only explicit administrative organization/account/membership provisioning uses the database directly. It requires the local `profitlens` database, checks existing workspace identity/access, preserves unchanged imports, and stops on conflicts instead of overwriting edited records. Do not rerun it after manually altering demo review state without reviewing those changes first.

Downloaded data and credentials remain under the existing Git-ignored `data/private/` path. Only the documentation and reproducible scripts are included in the repository; they contain no credentials. Workspace records are local database state and are not transferred by cloning the repository.

## Why the real workspace cannot populate every feature

The public council source has expense transactions but no customer sales ledger or verified customer allocations. Empty revenue/profit fields are meaningful missing-data states, not an import failure. Its public contract register cannot be treated as reviewed customer subscription contracts.

A follow-up source search on 15 October 2026 checked alternatives:

| Source | Evidence and suitability |
|---|---|
| [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) | Real retail invoice lines, customer IDs, quantities and sterling unit prices, CC BY 4.0. The documented schema has no operating-cost ledger, explicit VAT breakdown or linked contracts. Its 22.6 MB download was not fetched just to replace one incomplete view with another. |
| [Open Contracting](https://www.open-contracting.org/data/) | Supports contracting-process IDs and public procurement stages; a supplier's private customer profitability ledger is not established by those buyer-side records. |
| [Microsoft AdventureWorks](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure) | A sample database for demonstrations. It must not be presented as verified real ProfitLens customer activity. |
| [Microsoft Financial Sample](https://learn.microsoft.com/en-us/power-bi/create-reports/sample-financial-download) | A sample sales/profit table by segment and country, not linked source invoices, cost records and signed monthly customer contracts. |

No reusable source with all required linked real financial records was verified in this search. Do not fill the real workspace with invented invoices or inferred profit. The project owner subsequently required genuine data and rejected an expanded synthetic substitute; see the [follow-up source search and limitations](REAL_DATA_SOURCE_SEARCH.md). Existing synthetic workspaces remain separate: **ProfitLens Evaluation (synthetic)** is the larger six-month benchmark, and **Synthetic - Financial Demo (INR)** is the focused three-case teaching pack. Neither is a replacement for the requested real dataset.
