"""Create synthetic, Week 3-compatible files for a faculty demonstration."""

import argparse
import csv
import random
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1] / "demo-files"
CUSTOMER_FIELDS = ["customer_id", "name", "industry"]
INVOICE_FIELDS = [
    "invoice_id",
    "customer_id",
    "billing_period",
    "currency",
    "subtotal",
    "discount",
    "tax",
    "refund",
    "total",
]
EXPENSE_FIELDS = [
    "expense_id",
    "customer_id",
    "billing_period",
    "category",
    "amount",
    "currency",
]
PEOPLE = [
    ("DEMO3-C001", "Aster Design Demo", "Design services", "15000", "500"),
    ("DEMO3-C002", "Cedar Retail Demo", "Retail services", "22500", "0"),
    ("DEMO3-C003", "Bluebird Learning Demo", "Education services", "18000", "1000"),
    ("DEMO3-C004", "Maple Support Demo", "Customer support", "12000", "0"),
    ("DEMO3-C005", "Orchid Events Demo", "Event services", "30000", "1500"),
]


def amount(value):
    return f"{Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def write_csv(relative, fields, rows):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def invoice(identifier, customer="DEMO3-C001", period="2026-04", subtotal="1000"):
    return dict(
        invoice_id=identifier,
        customer_id=customer,
        billing_period=period,
        currency="INR",
        subtotal=amount(subtotal),
        discount="0.00",
        tax="0.00",
        refund="0.00",
        total=amount(subtotal),
    )


def contract(person, pages):
    customer, name, industry, rate, discount = person
    path = ROOT / "02-contracts" / f"{customer}_contract.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = canvas.Canvas(str(path), pagesize=A4, invariant=1)
    doc.setTitle(f"Synthetic monthly service contract - {customer}")
    doc.setAuthor("ProfitLens synthetic demo fixtures")

    def header(number, title):
        doc.setFillColor(HexColor("#16383D"))
        doc.rect(0, 752, 596, 90, fill=1, stroke=0)
        doc.setFillColor(HexColor("#A4E4D4"))
        doc.setFont("Helvetica-Bold", 10)
        doc.drawString(48, 811, "PROFITLENS  /  SYNTHETIC DEMO ONLY")
        doc.setFillColor(HexColor("#FFFFFF"))
        doc.setFont("Helvetica-Bold", 20)
        doc.drawString(48, 778, title)
        doc.setFillColor(HexColor("#5B7074"))
        doc.setFont("Helvetica", 9)
        doc.drawString(
            48,
            35,
            "Fictional parties and amounts. Not a real agreement or legal document.",
        )
        doc.drawRightString(547, 35, f"Page {number} of {pages}")

    def line(y, label, value):
        doc.setFillColor(HexColor("#16383D"))
        doc.setFont("Helvetica-Bold", 11)
        doc.drawString(48, y, label)
        doc.setFont("Helvetica", 11)
        doc.drawString(230, y, value)

    if pages == 2:
        header(1, "Service agreement overview")
        line(709, "Customer ID", customer)
        line(679, "Customer", name)
        line(649, "Sector", industry)
        line(619, "Provider", "ProfitLens Demo Services (fictional)")
        doc.setFont("Helvetica", 12)
        for i, text in enumerate(
            [
                "This file demonstrates page-level PDF evidence in ProfitLens.",
                "Scope: a fixed monthly service arrangement for sample records.",
                "Pricing, effective dates and review values are on page 2.",
                "Use page 2 as the source page when confirming reviewed terms.",
                "No customer data, signatures or real contractual obligations exist.",
            ]
        ):
            doc.drawString(48, 559 - i * 27, text)
        doc.showPage()
    header(pages, "Monthly service terms")
    for y, label, value in [
        (709, "Customer ID", customer),
        (679, "Customer", name),
        (649, "Provider", "ProfitLens Demo Services (fictional)"),
        (599, "Effective from", "2026-04-01"),
        (569, "Effective to", "2026-09-30"),
        (539, "Billing frequency", "monthly"),
        (509, "Currency", "INR"),
        (459, "Monthly rate (before tax)", amount(rate)),
        (429, "Monthly discount", amount(discount)),
        (399, "Rate less discount", amount(Decimal(rate) - Decimal(discount))),
        (349, "Review source page", str(pages)),
    ]:
        line(y, label, value)
    doc.setFont("Helvetica", 11)
    for i, text in enumerate(
        [
            "Taxes are recorded separately in the synthetic invoice CSV.",
            "Any invoice refund is recorded in that invoice's refund field.",
            "Review the values above manually before saving contract terms.",
            "Text extraction does not automatically verify or interpret a contract.",
        ]
    ):
        doc.drawString(48, 286 - i * 23, text)
    doc.save()


README = """# Teacher demo files - Week 3

**Everything in this folder is fictional, synthetic test data.** No real business data, passwords or signatures are included. Files match the currently implemented CSV and text-PDF workflows; Excel, images, scanned PDFs and Word files are not substitutes for these inputs.

Open this folder in File Explorer: `D:\\Profitlens\\demo-files`. Select the matching upload control in ProfitLens and browse to a file, or drop a file onto the native file input if your browser supports it. The whole page is not a general drop zone. Upload one file at a time.

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
.\\.venv\\Scripts\\python.exe scripts/generate_teacher_demo.py --overwrite
```

This rewrites only this generator's demo files. Keep manual variants in another folder. Requires the existing project Python dependencies (including ReportLab). Original `data/demo` fixtures are unchanged.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true", help="Regenerate this pack")
    args = parser.parse_args()
    if ROOT.exists() and any(ROOT.iterdir()) and not args.overwrite:
        parser.error(
            "demo-files already exists; use --overwrite to regenerate its fixtures"
        )
    ROOT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20261010)
    customers, invoices, expenses = [], [], []
    for index, (customer, name, industry, rate, discount) in enumerate(PEOPLE, 1):
        customers.append(dict(customer_id=customer, name=name, industry=industry))
        for month in range(4, 10):
            period = f"2026-{month:02d}"
            row = invoice(
                f"DEMO3-I-{index:03d}-2026{month:02d}", customer, period, rate
            )
            row["discount"] = amount(discount)
            row["refund"] = "250.00" if index == 1 and month == 5 else "0.00"
            if index == 5 and month == 9:
                row.update(subtotal="0.00", discount="0.00", refund="0.00")
            base = (
                Decimal(row["subtotal"])
                - Decimal(row["discount"])
                - Decimal(row["refund"])
            )
            row["tax"] = amount(base * Decimal("0.18"))
            row["total"] = amount(base + Decimal(row["tax"]))
            invoices.append(row)
            for part, category, cost in [
                (
                    1,
                    "Service delivery",
                    Decimal(rate) * Decimal(rng.randint(35, 55)) / 100,
                ),
                (2, "Cloud tools", Decimal(rng.randint(40000, 180000)) / 100),
            ]:
                expenses.append(
                    dict(
                        expense_id=f"DEMO3-E-{index:03d}-2026{month:02d}-{part}",
                        customer_id=customer,
                        billing_period=period,
                        category=category,
                        amount=amount(cost),
                        currency="INR",
                    )
                )
    write_csv("01-valid-data/01-customers.csv", CUSTOMER_FIELDS, customers)
    write_csv("01-valid-data/02-invoices.csv", INVOICE_FIELDS, invoices)
    write_csv("01-valid-data/03-expenses.csv", EXPENSE_FIELDS, expenses)
    for index, person in enumerate(PEOPLE[:3]):
        contract(person, 2 if index == 1 else 1)
    invalid = [
        (
            "01-invoices-wrong-total.csv",
            [invoice("DEMO3-BAD-TOTAL") | {"total": "999.00"}],
        ),
        (
            "02-invoices-invalid-month.csv",
            [invoice("DEMO3-BAD-MONTH", period="2026-13")],
        ),
        (
            "03-invoices-unknown-customer.csv",
            [invoice("DEMO3-BAD-CUSTOMER", customer="DEMO3-MISSING")],
        ),
        (
            "04-invoices-duplicate-id.csv",
            [invoice("DEMO3-BAD-DUP"), invoice("DEMO3-BAD-DUP")],
        ),
        (
            "05-invoices-wrong-currency.csv",
            [invoice("DEMO3-BAD-CURRENCY") | {"currency": "USD"}],
        ),
        (
            "08-invoices-mixed-valid-invalid.csv",
            [invoice("DEMO3-MIX-GOOD"), invoice("DEMO3-MIX-BAD") | {"total": "999.00"}],
        ),
    ]
    for name, rows in invalid:
        write_csv(f"03-validation-errors/{name}", INVOICE_FIELDS, rows)
    write_csv(
        "03-validation-errors/06-invoices-missing-column.csv",
        [field for field in INVOICE_FIELDS if field != "refund"],
        [
            {
                key: value
                for key, value in invoice("DEMO3-BAD-COLUMN").items()
                if key != "refund"
            }
        ],
    )
    write_csv(
        "03-validation-errors/07-expenses-negative-amount.csv",
        EXPENSE_FIELDS,
        [
            dict(
                expense_id="DEMO3-BAD-EXPENSE",
                customer_id="DEMO3-C001",
                billing_period="2026-04",
                category="Service delivery",
                amount="-100.00",
                currency="INR",
            ),
        ],
    )
    write_csv("04-retry-and-conflict/01-invoices-repeat.csv", INVOICE_FIELDS, invoices)
    conflict = invoices[0] | {
        "subtotal": amount(Decimal(invoices[0]["subtotal"]) + 100),
        "total": amount(Decimal(invoices[0]["total"]) + 100),
    }
    write_csv(
        "04-retry-and-conflict/02-invoice-existing-id-conflict.csv",
        INVOICE_FIELDS,
        [conflict],
    )
    (ROOT / "README.md").write_text(README, encoding="utf-8")
    print(
        f"Created {ROOT}: 5 customers, 30 invoices, 60 expenses, 3 PDFs, 8 invalid CSVs and 2 retry/conflict CSVs."
    )


if __name__ == "__main__":
    main()
