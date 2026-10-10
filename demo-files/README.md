# Teacher demo files - Week 3

**Everything in this folder is fictional, synthetic test data.** No real business data, passwords or signatures are included. Files match the currently implemented CSV and text-PDF workflows; Excel, images, scanned PDFs and Word files are not substitutes for these inputs.

Open this folder in File Explorer: `D:\Profitlens\demo-files`. Select the matching upload control in ProfitLens and browse to a file, or drop a file onto the native file input if your browser supports it. The whole page is not a general drop zone. Upload one file at a time.

## 1. Import the valid files in this order

Sign in as **admin or finance** in an **INR workspace**, such as the existing synthetic demo workspace. Go to **Imports**, choose the matching record type, select the file, click **Preview import**, then **Confirm import**.

| Order | File in `01-valid-data/` | Import type | First import into a workspace without these IDs |
| --- | --- | --- | --- |
| 1 | `01-customers.csv` | Customers | 5 customers |
| 2 | `02-invoices.csv` | Invoices | 30 invoices across April-September 2026 |
| 3 | `03-expenses.csv` | Expenses | 60 attributed expenses, two per customer/month |

The default dashboard dataset is preloaded separately with original C001/C002 and `READY-` IDs. This upload pack is never imported by the seed command. IDs begin with `DEMO3-` so they do not collide with the original C001/C002 seed. These counts are additions, not total dashboard counts; existing records remain. Later imports are skipped/deduplicated where unchanged. Edited existing IDs can cause conflicts. Import customers first or invoice/expense references will fail.

The amounts vary reproducibly. Included examples cover discounts, a pre-tax refund, cents and one valid zero-value invoice (Orchid, September). Invoice tax values are synthetic inputs for validation, not tax guidance. The current overview counts records; it does not calculate revenue, contribution or margin.

## 2. Upload and review contract PDFs

Go to **Contracts**, select the matching customer, choose the PDF from `02-contracts/`, and upload it. Inspect the source text/PDF, then enter these terms manually:

| PDF / customer | Monthly rate | Monthly discount | Source page |
| --- | --- | --- | --- |
| `DEMO3-C001_contract.pdf` - Aster Design Demo | 15000.00 | 500.00 | 1 |
| `DEMO3-C002_contract.pdf` - Cedar Retail Demo | 22500.00 | 0.00 | 2 |
| `DEMO3-C003_contract.pdf` - Bluebird Learning Demo | 18000.00 | 1000.00 | 1 |

For all three: **currency INR**, **billing monthly**, **effective from 2026-04-01**, **effective to 2026-09-30**. Enter the original rate and discount separately. Cedar intentionally has two pages so you can demonstrate a real page-2 source reference. Maple and Orchid deliberately have no supplied contract. Re-uploading identical bytes for the same customer should reuse the existing contract. Existing overlapping reviewed terms for that customer may block review.

## 3. Show useful validation errors

Import valid customers first. Open a file from `03-validation-errors/` with the specified type. **These should show an invalid preview and cannot be confirmed.** Do not use them for your first successful import.

| File | Type | Intentional issue |
| --- | --- | --- |
| `01-invoices-wrong-total.csv` | Invoices | Total does not match subtotal - discount + tax - refund |
| `02-invoices-invalid-month.csv` | Invoices | Month is 2026-13 |
| `03-invoices-unknown-customer.csv` | Invoices | Referenced customer does not exist |
| `04-invoices-duplicate-id.csv` | Invoices | Same invoice ID occurs twice in the file |
| `05-invoices-wrong-currency.csv` | Invoices | USD conflicts with the INR workspace |
| `06-invoices-missing-column.csv` | Invoices | Required refund column is absent |
| `07-expenses-negative-amount.csv` | Expenses | Negative expense amount |
| `08-invoices-mixed-valid-invalid.csv` | Invoices | One valid row and one invalid total; the whole batch is blocked |

Preview can save batch metadata and issues. It does **not** insert these rows into business records. Wrong-currency rejection depends on using INR as instructed.

## 4. Demonstrate retry and ID conflict

After the valid invoices are confirmed:

- Upload `04-retry-and-conflict/01-invoices-repeat.csv` as **Invoices**. It is byte-for-byte identical to the valid invoice file despite its name. The prior confirmed batch/result is returned; no new invoices should appear. That saved result may still display its original inserted count - verify the unchanged record count rather than treating it as a new insertion.
- Upload `04-retry-and-conflict/02-invoice-existing-id-conflict.csv` as **Invoices**. It uses the first existing invoice ID with a different, internally valid amount. Expect a conflict in preview rather than a silent overwrite. Before the original invoices exist, this is a valid record, so run it only at this stage.

## Five-minute faculty demonstration

1. Import the three valid CSVs; show the new customers and six months of record activity.
2. Open one invoice and inspect its imported filename/row source.
3. Preview a wrong-total file and the mixed-valid/invalid file; explain why nothing is partly confirmed.
4. Repeat the invoice file; show the unchanged count. Then show the existing-ID conflict.
5. Upload Cedar's contract, select source page 2 and confirm manually reviewed terms.
6. Optional: in **Team access**, assign DEMO3-C001 to the analyst, then sign in as that analyst. The existing C001 assignment does not automatically grant this new customer. Restore assignments afterwards if desired.

## Repeat or recreate the pack

Reusing the same IDs demonstrates deduplication; it is not a reset. For a fresh insertion demonstration, use a fresh prepared synthetic workspace or consistently rename customer and dependent record IDs. Do not wipe a working database just to repeat the demo.

The generator uses a fixed random seed and deterministic PDF metadata. From the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/generate_teacher_demo.py --overwrite
```

This rewrites only this generator's demo files. Keep manual variants in another folder. Requires the existing project Python dependencies (including ReportLab). Original `data/demo` fixtures are unchanged.
