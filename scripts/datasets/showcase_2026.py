"""Deterministic synthetic showcase using normal authenticated preview/confirm APIs.

Call populate(client, workspace_api_path) only in a designated synthetic workspace.
No credentials, direct business-table writes, external model calls or real company claims.
"""

import csv
from decimal import Decimal
from pathlib import Path

from reportlab.pdfgen import canvas

ROOT = Path("demo-files/showcase-2026")
NAMES = [
    "Aster Design",
    "Cedar Logistics",
    "Harbor Analytics",
    "Juniper Studio",
    "Maple Retail",
    "Orion Consulting",
    "Pine Support",
    "Willow Digital",
]


def write_csv(name, rows):
    ROOT.mkdir(parents=True, exist_ok=True)
    path = ROOT / name
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return path


def prepare():
    customers = [
        {
            "customer_id": f"S{i:02}",
            "name": name + " (Synthetic)",
            "industry": "B2B services demo",
        }
        for i, name in enumerate(NAMES, 1)
    ]
    invoices = []
    expenses = []
    for i in range(1, 7):
        for month in range(5, 11):
            rate = Decimal(12000 + i * 3000)
            subtotal = rate + (Decimal(1200) if i == 2 and month == 10 else 0)
            cost = (
                rate * Decimal(".52") + Decimal((month - 5) * 140 + i * 80)
            ).quantize(Decimal(".01"))
            if i == 3 and month == 10:
                cost += Decimal(7000)
            invoices.append(
                {
                    "invoice_id": f"SYN-I-{i:02}-{month:02}",
                    "customer_id": f"S{i:02}",
                    "billing_period": f"2026-{month:02}",
                    "currency": "INR",
                    "subtotal": str(subtotal),
                    "discount": "0",
                    "tax": str(subtotal * Decimal(".18")),
                    "refund": "0",
                    "total": str(subtotal * Decimal("1.18")),
                }
            )
            for category, weight in [
                ("Delivery labour", Decimal(".8")),
                ("Hosting and tools", Decimal(".2")),
            ]:
                expenses.append(
                    {
                        "expense_id": f"SYN-E-{i:02}-{month:02}-{len(expenses)}",
                        "customer_id": f"S{i:02}",
                        "billing_period": f"2026-{month:02}",
                        "currency": "INR",
                        "category": category,
                        "amount": str((cost * weight).quantize(Decimal(".01"))),
                    }
                )
    paths = {
        k: write_csv(k + ".csv", v)
        for k, v in [
            ("customers", customers),
            ("invoices", invoices),
            ("expenses", expenses),
        ]
    }
    write_csv(
        "new-import-invoices.csv",
        [
            {
                "invoice_id": "SYN-NEW-NOV-S01",
                "customer_id": "S01",
                "billing_period": "2026-11",
                "currency": "INR",
                "subtotal": "15000",
                "discount": "0",
                "tax": "2700",
                "refund": "0",
                "total": "17700",
            }
        ],
    )
    for i in range(1, 5):
        path = ROOT / f"synthetic-contract-S{i:02}.pdf"
        if not path.exists():
            c = canvas.Canvas(str(path), invariant=1)
            c.setFont("Helvetica", 12)
            for y, line in enumerate(
                [
                    "SYNTHETIC DEMO CONTRACT - no legal effect",
                    f"Customer S{i:02}: {NAMES[i - 1]}",
                    f"Fixed monthly service fee: INR {12000 + i * 3000}.00 excluding tax.",
                    "Monthly discount: INR 0.00.",
                    "Effective 1 May 2026 through 31 December 2026.",
                    "Payment terms: 30 days from invoice issue.",
                    "This fictional agreement is solely for ProfitLens demonstration.",
                ]
            ):
                c.drawString(45, 780 - y * 30, line)
            c.save()
    return paths


def request(c, method, path, **kwargs):
    r = c.request(method, path, **kwargs)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path}: {r.status_code} {r.text[:500]}")
    return r.json()


def populate(c, base):
    paths = prepare()
    for kind, path in paths.items():
        batch = request(
            c,
            "POST",
            base + f"/imports/{kind}/preview",
            files={"file": (path.name, path.read_bytes(), "text/csv")},
        )
        assert not batch["issues"], batch["issues"]
        request(c, "POST", base + f"/imports/{batch['id']}/confirm")
    contracts = request(c, "GET", base + "/contracts")
    for i in range(1, 5):
        path = ROOT / f"synthetic-contract-S{i:02}.pdf"
        contract = next((x for x in contracts if x["filename"] == path.name), None)
        if contract is None:
            contract = request(
                c,
                "POST",
                base + "/contracts",
                data={"customer_id": f"S{i:02}"},
                files={"file": (path.name, path.read_bytes(), "application/pdf")},
            )
        if contract["state"] != "reviewed":
            request(
                c,
                "PUT",
                base + f"/contracts/{contract['id']}/terms",
                json={
                    "effective_from": "2026-05-01",
                    "effective_to": "2026-12-31",
                    "currency": "INR",
                    "monthly_rate": str(12000 + i * 3000),
                    "monthly_discount": "0",
                    "source_page": 1,
                },
            )
    for month in (9, 10):
        report = request(
            c, "GET", base + f"/profitability?billing_period=2026-{month:02}"
        )
        for item in report["items"]:
            if item["customer_id"] not in {"S01", "S02", "S03", "S04", "S05"}:
                continue  # deliberate incomplete-cost review example
            request(
                c,
                "PUT",
                base
                + f"/profitability/{item['customer_id']}/2026-{month:02}/cost-review",
                json={
                    "input_hash": item["cost_input_hash"],
                    "note": "Synthetic ground-truth fixture: all defined direct costs for this period reviewed.",
                },
            )
    vendors = request(c, "GET", base + "/operations/vendors")
    for i, name in enumerate(
        ["Cloud Hosting", "Design Supplies", "Equipment Partner"], 1
    ):
        if not any(x["vendor_id"] == f"V{i}" for x in vendors):
            request(
                c,
                "POST",
                base + "/operations/vendors",
                json={"vendor_id": f"V{i}", "name": name + " (Synthetic)"},
            )
    items = request(c, "GET", base + "/operations/items")
    for i, name, price in [
        (1, "Support hours", "1500"),
        (2, "Workspace equipment", "12000"),
        (3, "Cloud hosting month", "4500"),
    ]:
        if not any(x["item_id"] == f"ITEM{i}" for x in items):
            request(
                c,
                "POST",
                base + "/operations/items",
                json={
                    "item_id": f"ITEM{i}",
                    "name": name,
                    "unit_price": price,
                    "currency": "INR",
                },
            )
    recurring = request(c, "GET", base + "/planning/recurring")
    for i in (7, 8):
        if not any(x["id"] == f"RET-{i}" for x in recurring["schedules"]):
            request(
                c,
                "POST",
                base + "/planning/recurring",
                json={
                    "id": f"RET-{i}",
                    "name": NAMES[i - 1] + " monthly support",
                    "customer_id": f"S{i:02}",
                    "start_on": "2026-11-01",
                    "end_on": "2027-04-01",
                    "currency": "INR",
                    "subtotal": str(10000 + i * 1000),
                    "tax": str((10000 + i * 1000) * Decimal(".18")),
                },
            )
    request(c, "POST", base + "/planning/recurring/generate")
    recurring = request(c, "GET", base + "/planning/recurring")
    draft = next(
        x
        for x in recurring["drafts"]
        if x["schedule_id"] == "RET-7" and x["issued_on"] == "2026-11-01"
    )
    request(c, "POST", base + f"/planning/drafts/{draft['id']}/issue")
    orders = request(c, "GET", base + "/planning/orders")
    for i in range(1, 4):
        key = f"PO-DEMO-{i}"
        if not any(x["id"] == key for x in orders):
            request(
                c,
                "POST",
                base + "/planning/orders",
                json={
                    "id": key,
                    "vendor_id": f"V{i}",
                    "ordered_on": "2026-10-20",
                    "expected_on": "2026-11-10",
                    "currency": "INR",
                    "notes": "Synthetic demo purchase; not automatically a customer expense.",
                    "lines": [
                        {
                            "description": "Demonstration service / equipment",
                            "quantity": str(i + 1),
                            "unit_price": str(3000 + i * 500),
                            "tax": "0",
                        }
                    ],
                },
            )
        current = next(
            x for x in request(c, "GET", base + "/planning/orders") if x["id"] == key
        )
        if i < 3 and current["state"] == "draft":
            request(c, "POST", base + f"/planning/orders/{key}/approve")
        if i == 1:
            request(
                c,
                "PUT",
                base + f"/planning/orders/{key}/bill",
                json={
                    "bill_id": "SYN-BILL-01",
                    "issued_on": "2026-10-25",
                    "due_on": "2026-11-15",
                    "opening_paid": "0",
                    "payments_complete": True,
                    "invoice_matches_order": True,
                },
            )
    tracked = request(c, "GET", base + "/operations/invoice-candidates")
    payments = request(c, "GET", base + "/operations/payments")
    for i in range(1, 7):
        key = f"SYN-I-{i:02}-10"
        if not next(x for x in tracked if x["invoice_id"] == key)["tracked"]:
            request(
                c,
                "PUT",
                base + f"/operations/invoice-terms/{key}",
                json={
                    "due_on": "2026-11-15" if i % 2 else "2026-10-30",
                    "opening_paid": "0",
                    "payments_complete": True,
                },
            )
        if i < 5 and not any(x["payment_id"] == f"RECEIPT-{i}" for x in payments):
            request(
                c,
                "POST",
                base + "/operations/payments",
                json={
                    "payment_id": f"RECEIPT-{i}",
                    "direction": "received",
                    "paid_on": "2026-10-28",
                    "currency": "INR",
                    "allocations": [{"document_id": key, "amount": "5000"}],
                },
            )
    if not any(x["payment_id"] == "SUPPLIER-PAYMENT" for x in payments):
        request(
            c,
            "POST",
            base + "/operations/payments",
            json={
                "payment_id": "SUPPLIER-PAYMENT",
                "direction": "made",
                "paid_on": "2026-10-28",
                "currency": "INR",
                "allocations": [{"document_id": "SYN-BILL-01", "amount": "2000"}],
            },
        )
    return {
        "dashboard": request(c, "GET", base + "/dashboard"),
        "balances": request(c, "GET", base + "/operations/summary"),
    }


if __name__ == "__main__":
    prepare()
    print("Prepared labelled synthetic CSVs, PDFs and an unimported November invoice.")
