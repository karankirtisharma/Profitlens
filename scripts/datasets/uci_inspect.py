"""Inspect the official UCI workbook and preserve a bounded, source-linked sample.

No tax assumptions, invented costs, or dashboard writes. Download the original
UCI 352 archive into data/private/uci-online-retail/online-retail.zip first.
"""

import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path("data/private/uci-online-retail")
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def inspect():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    assert (
        hashlib.sha256((ROOT / "online-retail.zip").read_bytes()).hexdigest()
        == manifest["sha256"]
    )
    with ZipFile(ROOT / "online-retail.zip") as archive:
        names = [n for n in archive.namelist() if n.endswith(".xlsx")]
        assert len(names) == 1
        workbook = archive.read(names[0])
    with ZipFile(io.BytesIO(workbook)) as book:
        strings = []
        with book.open("xl/sharedStrings.xml") as stream:
            for _, node in ET.iterparse(stream, events=("end",)):
                if node.tag == NS + "si":
                    strings.append("".join(t.text or "" for t in node.iter(NS + "t")))
                    node.clear()
        counts = Counter()
        invoices = defaultdict(list)
        customers, months = set(), set()
        with book.open("xl/worksheets/sheet1.xml") as stream:
            for _, node in ET.iterparse(stream, events=("end",)):
                if node.tag != NS + "row":
                    continue
                cells = {}
                for cell in node.findall(NS + "c"):
                    value = cell.findtext(NS + "v", "")
                    cells["".join(c for c in cell.attrib["r"] if c.isalpha())] = (
                        strings[int(value)] if cell.get("t") == "s" else value
                    )
                row_number = int(node.attrib["r"])
                node.clear()
                if row_number == 1:
                    headers = cells
                    continue
                counts["source_rows"] += 1
                invoice, customer = cells.get("A", ""), cells.get("G", "")
                quantity, price = (
                    Decimal(cells.get("D", "0")),
                    Decimal(cells.get("F", "0")),
                )
                stamp = datetime(1899, 12, 30) + timedelta(days=float(cells["E"]))
                month = stamp.strftime("%Y-%m")
                months.add(month)
                if customer:
                    customers.add(customer)
                else:
                    counts["missing_customer_rows"] += 1
                if invoice.upper().startswith("C"):
                    counts["cancellation_rows"] += 1
                if quantity <= 0 or price <= 0:
                    counts["nonpositive_quantity_or_price_rows"] += 1
                invoices[invoice].append(
                    {
                        "source_row": row_number,
                        "InvoiceNo": invoice,
                        "StockCode": cells.get("B", ""),
                        "Description": cells.get("C", ""),
                        "Quantity": str(quantity),
                        "UnitPrice": str(price),
                        "InvoiceDate": stamp.isoformat(),
                        "CustomerID": customer,
                        "Country": cells.get("H", ""),
                        "month": month,
                        "reported_line_value_GBP": str(quantity * price),
                    }
                )
        # Whole invoices only; avoid partial totals and ambiguous duplicated source lines.
        candidates = []
        for invoice, lines in invoices.items():
            keys = [
                tuple((k, v) for k, v in r.items() if k != "source_row") for r in lines
            ]
            if len(set(keys)) != len(keys):
                counts["invoices_with_exact_duplicate_lines"] += 1
                continue
            if (
                invoice.upper().startswith("C")
                or not invoice.isdigit()
                or any(
                    not r["CustomerID"]
                    or Decimal(r["Quantity"]) <= 0
                    or Decimal(r["UnitPrice"]) <= 0
                    for r in lines
                )
                or len({(r["CustomerID"], r["InvoiceDate"]) for r in lines}) != 1
            ):
                continue
            if "2011-01" <= lines[0]["month"] <= "2011-11":
                candidates.append((invoice, lines))
        by_customer = defaultdict(list)
        for _, lines in candidates:
            by_customer[lines[0]["CustomerID"]].extend(lines)
        cohort = sorted(
            cid
            for cid, lines in by_customer.items()
            if len({r["month"] for r in lines}) >= 4 and 40 <= len(lines) <= 140
        )[:12]
        per_month = Counter()
        selected = []
        for _invoice, lines in sorted(
            candidates, key=lambda pair: pair[1][0]["InvoiceDate"]
        ):
            month = lines[0]["month"]
            if lines[0]["CustomerID"] in cohort:
                selected.extend(lines)
                per_month[month] += 1
        assert len(selected) <= 2000
        with (ROOT / "source-linked-sales-sample.csv").open(
            "w", newline="", encoding="utf8"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=list(selected[0]))
            writer.writeheader()
            writer.writerows(selected)
        report = {
            "headers": headers,
            **counts,
            "distinct_invoices_in_source": len(invoices),
            "distinct_known_customers_in_source": len(customers),
            "source_months": sorted(months),
            "sample_invoices": sum(per_month.values()),
            "sample_customers": len({r["CustomerID"] for r in selected}),
            "sample_lines": len(selected),
            "sample_invoices_by_month": dict(per_month),
            "sample_reported_sales_value_GBP": str(
                sum(
                    (Decimal(r["reported_line_value_GBP"]) for r in selected),
                    Decimal(0),
                )
            ),
            "selection": "Fixed cohort: first 12 sorted anonymous customer IDs with eligible positive invoices in at least four months and 40-140 source lines in Jan-Nov 2011. All eligible whole invoices for that cohort; cancellations, zero/negative records and invoices with duplicate/conflicting lines excluded. Not a representative business sample.",
            "limitations": [
                "No cost ledger or customer cost allocation",
                "No contracts or PDF invoices",
                "No explicit tax, discount or refund breakdown; do not default these to zero",
                "Cancellations are not matched refunds",
                "Anonymous customer IDs, not verified business names",
            ],
            "dashboard_import": "Prepared as reported_sales with unknown financial breakdown. Import requires separate authenticated preview and confirmation.",
        }
        prepared = ROOT / "prepared"
        prepared.mkdir(exist_ok=True)

        def write(name, records):
            with (prepared / name).open("w", newline="", encoding="utf8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(records[0]))
                writer.writeheader()
                writer.writerows(records)

        write(
            "customers.csv",
            [
                {
                    "customer_id": cid,
                    "name": f"Customer {cid} (anonymous)",
                    "source_url": manifest["source"],
                    "source_customer_id": cid,
                }
                for cid in cohort
            ],
        )
        groups = defaultdict(list)
        for r in selected:
            groups[r["InvoiceNo"]].append(r)
        normalized = []
        for invoice, lines in sorted(groups.items()):
            raw = sum(
                (Decimal(r["Quantity"]) * Decimal(r["UnitPrice"]) for r in lines),
                Decimal(0),
            )
            normalized.append(
                {
                    "invoice_id": invoice,
                    "customer_id": lines[0]["CustomerID"],
                    "billing_period": lines[0]["month"],
                    "currency": "GBP",
                    "total": str(raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                    "amount_basis": "reported_sales",
                    "source_url": manifest["source"],
                    "source_invoice_no": invoice,
                    "source_rows": ";".join(str(r["source_row"]) for r in lines),
                    "source_raw_sales_sum": str(raw),
                    "source_invoice_date": lines[0]["InvoiceDate"],
                    "source_country": lines[0]["Country"],
                    "source_rounding": "Sum original quantity times price; round invoice sum HALF_UP to GBP 0.01; no tax assumption",
                }
            )
        write("invoices.csv", normalized[:-3])
        write("demo-new-imports.csv", normalized[-3:])
        initial = normalized[:-3]
        report["preloaded_invoices"] = len(initial)
        report["new_import_invoices"] = 3
        report["preloaded_reported_sales_GBP"] = str(
            sum((Decimal(r["total"]) for r in initial), Decimal(0))
        )
        report["preloaded_month_totals"] = {
            month: str(
                sum(
                    (
                        Decimal(r["total"])
                        for r in initial
                        if r["billing_period"] == month
                    ),
                    Decimal(0),
                )
            )
            for month in sorted(per_month)
        }
        report["cohort"] = cohort
        (ROOT / "inspection.json").write_text(
            json.dumps(report, indent=2), encoding="utf8"
        )
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    inspect()
