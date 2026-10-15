"""Bounded public-data download and loss-aware preparation; never calls an AI service."""

import argparse
import csv
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import httpx
from pypdf import PdfReader

ROOT = Path("data/private/real-world-fhdc-2025")
BASE = "https://www.folkestone-hythe.gov.uk"
SOURCES = {
    "procurement-2025-04.csv": BASE
    + "/downloads/file/5928/procurement-data-april-2025",
    "procurement-2025-05.csv": BASE + "/downloads/file/5992/procurement-data-may-2025",
    "procurement-2025-09.csv": BASE
    + "/downloads/file/6185/procurement-data-september-2025",
    "procurement-2025-12.csv": BASE
    + "/downloads/file/6332/procurement-data-december-2025",
    "contract-register-2026-08.pdf": BASE
    + "/downloads/file/6741/contract-register-24august2026",
    "licence-source.html": BASE + "/council-transparency/councils-publication-scheme",
}
BUCKET = "UNALLOCATED-PUBLIC-SPEND"
LIBRARY = "UNLINKED-PUBLIC-REGISTER"
EXPENSE_FIELDS = [
    "expense_id",
    "customer_id",
    "billing_period",
    "category",
    "amount",
    "currency",
]


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def csv_write(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def download(root):
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    by_name = {v["file"]: v for v in manifest}
    (root / "originals").mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=45, follow_redirects=False) as client:
        for name, url in SOURCES.items():
            path = root / "originals" / name
            if path.exists():
                if (
                    name not in by_name
                    or hashlib.sha256(path.read_bytes()).hexdigest()
                    != by_name[name]["sha256"]
                ):
                    raise RuntimeError(
                        f"Original hash mismatch: {name}; never overwritten"
                    )
                continue
            data = bytearray()
            with client.stream("GET", url) as r:
                r.raise_for_status()
                for chunk in r.iter_bytes():
                    data.extend(chunk)
                    if len(data) > 2 * 1024 * 1024:
                        raise RuntimeError("2 MiB per-file limit exceeded")
            path.write_bytes(data)
            manifest.append(
                dict(
                    file=name,
                    url=url,
                    downloaded_at=datetime.now(timezone.utc).isoformat(),
                    bytes=len(data),
                    sha256=hashlib.sha256(data).hexdigest(),
                    content_type=r.headers.get("content-type"),
                )
            )
            dump(manifest_path, manifest)
    return manifest


def money(text):
    text = text.strip().replace(",", "").replace("£", "")
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    value = Decimal(text)
    if not value.is_finite() or value != value.quantize(Decimal("0.01")):
        raise ValueError("Non-cent money requires review")
    return value


def prepare(root):
    manifest = download(root)
    originals = {x["file"]: x for x in manifest}
    rows, excluded, logs, file_stats = [], [], [], []
    fingerprints = Counter()
    period_totals = defaultdict(lambda: Decimal(0))
    raw_fields = [
        "service_area",
        "description",
        "transaction_date",
        "net_amount",
        "vat",
        "gross",
        "supplier",
    ]
    for name in SOURCES:
        if not name.startswith("procurement"):
            continue
        path = root / "originals" / name
        assert path.read_bytes().startswith(b"%PDF"), (
            "Source format changed; review adapter"
        )
        reader = PdfReader(path)
        assert len(reader.pages) == 1, "Source layout changed; review adapter"
        text = reader.pages[0].extract_text(extraction_mode="layout")
        (root / "extracted").mkdir(exist_ok=True)
        (root / "extracted" / (name + ".txt")).write_text(text, encoding="utf-8")
        dated = [
            line for line in text.splitlines() if re.search(r"\d{2}/\d{2}/\d{4}", line)
        ]
        totals = [Decimal(0)] * 3
        for position, line in enumerate(dated, 1):
            cells = re.split(r"\s{2,}", line.strip())
            assert len(cells) == 7, (name, position, "Unexpected table columns")
            raw = dict(zip(raw_fields, cells, strict=True))
            day = datetime.strptime(raw["transaction_date"], "%d/%m/%Y").date()
            amounts = [money(raw[k]) for k in ("net_amount", "vat", "gross")]
            totals = [a + b for a, b in zip(totals, amounts, strict=True)]
            key = "FHDC-" + name[12:19].replace("-", "") + f"-P1-R{position:03}"
            # The source has no stable invoice/transaction IDs. Use explicit provenance IDs.
            target = dict(
                expense_id=key,
                customer_id=BUCKET,
                billing_period=day.strftime("%Y-%m"),
                category=raw["description"],
                amount=f"{amounts[0]:.2f}",
                currency="GBP",
            )
            reasons = []
            if amounts[0] + amounts[1] != amounts[2]:
                reasons.append("source_net_plus_vat_not_equal_gross")
            if amounts[0] < 0:
                reasons.append("negative_credit_not_supported_by_expense_schema")
            if any(not x.strip() for x in cells):
                reasons.append("missing_source_field")
            fingerprints[tuple(cells)] += 1
            event = dict(
                source_file=name,
                source_sha256=originals[name]["sha256"],
                source_url=SOURCES[name],
                source_page=1,
                source_transaction_row=position,
                original=raw,
                target=target,
                disposition="excluded" if reasons else "included",
                reasons=reasons,
                transformations=[
                    "layout columns -> named fields",
                    "DD/MM/YYYY -> transaction calendar month (not publication month)",
                    "comma/parenthesis money -> exact Decimal cents",
                    "source Amount -> expense amount; VAT not deducted again",
                    "GBP inferred from UK council reporting; no conversion",
                    "technical unallocated bucket; not an actual customer allocation",
                    "generated source-coordinate ID; no source ID exists",
                ],
            )
            if reasons:
                excluded.append(event)
            else:
                event["target_csv_row"] = len(rows) + 2
                rows.append(target)
                period_totals[target["billing_period"]] += amounts[0]
            logs.append(event)
        footer = next(line for line in text.splitlines() if "Total:" in line)
        footer_values = [money(x) for x in re.findall(r"-?\d[\d,]*\.\d{2}", footer)]
        assert len(footer_values) == 3
        assert totals == footer_values, (
            name,
            "Extracted rows do not reconcile to source footer; review before import",
        )
        file_stats.append(
            dict(
                file=name,
                actual_format="PDF (despite CSV label/extension)",
                pages=1,
                transaction_rows=len(dated),
                printed_totals=[str(x) for x in footer_values],
                extracted_sums=[str(x) for x in totals],
                footer_reconciles=totals == footer_values,
                row_reconciliation_errors=sum(
                    "source_net_plus_vat_not_equal_gross" in v["reasons"]
                    for v in logs
                    if v["source_file"] == name
                ),
                missing_values=sum(
                    any(not x.strip() for x in v["original"].values())
                    for v in logs
                    if v["source_file"] == name
                ),
            )
        )
    real = root / "prepared" / "real"
    csv_write(
        real / "customers.csv",
        ["customer_id", "name", "industry"],
        [
            dict(
                customer_id=BUCKET,
                name="TECHNICAL BUCKET - public unallocated spend (not a customer)",
                industry="Unallocated procurement; debit subset only",
            ),
            dict(
                customer_id=LIBRARY,
                name="REFERENCE ONLY - unlinked public contract register",
                industry="No transaction linkage or reviewed pricing",
            ),
        ],
    )
    csv_write(real / "expenses.csv", EXPENSE_FIELDS, rows)
    shutil.copyfile(
        root / "originals" / "contract-register-2026-08.pdf",
        real / "UNLINKED-contract-register.pdf",
    )
    with (root / "transformations.jsonl").open("w", encoding="utf-8") as f:
        for event in logs:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    dump(root / "excluded-records.json", excluded)
    # Existing synthetic records are copied, never joined to the council data.
    synthetic = root / "prepared" / "synthetic-companion"
    ids = {"EVAL-01", "EVAL-06", "EVAL-11"}
    for kind in ("customers", "invoices", "expenses"):
        with Path(f"demo-files/evaluation/{kind}.csv").open(
            encoding="utf-8-sig", newline=""
        ) as f:
            reader = csv.DictReader(f)
            selected = [
                r
                for r in reader
                if r["customer_id"] in ids
                and (
                    kind == "customers" or r["billing_period"] in {"2026-08", "2026-09"}
                )
            ]
            csv_write(synthetic / f"{kind}.csv", reader.fieldnames, selected)
    for cid in sorted(ids):
        shutil.copyfile(
            Path("demo-files/evaluation") / f"{cid}-current.pdf",
            synthetic / f"{cid}-current.pdf",
        )
    register = PdfReader(root / "originals" / "contract-register-2026-08.pdf")
    register_text = "\n".join(p.extract_text() for p in register.pages)
    (root / "extracted" / "contract-register.txt").write_text(
        register_text, encoding="utf-8"
    )
    profile = dict(
        source_rows=len(logs),
        imported_expense_candidates=len(rows),
        excluded_rows=len(excluded),
        exact_duplicate_extra_rows=sum(v - 1 for v in fingerprints.values() if v > 1),
        duplicate_policy="Retained: equal values do not prove same purchase; IDs use source coordinates",
        missing_invoice_ids=len(logs),
        missing_customer_allocations=len(logs),
        missing_contract_links=len(logs),
        currency="GBP inferred; source does not have ISO currency column",
        file_profiles=file_stats,
        expected_period_costs={k: f"{v:.2f}" for k, v in sorted(period_totals.items())},
        expected_positive_subset_total=f"{sum(period_totals.values()):.2f}",
        register_pages=len(register.pages),
        register_record_count="Not asserted: multi-page table is retained as unlinked reference, not normalized records",
        licence="Open Government Licence v3.0; explicit council publication scheme, original HTML retained",
        licence_url="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        attribution="Contains public sector information licensed under the Open Government Licence v3.0. Source: Folkestone & Hythe District Council.",
    )
    dump(root / "profile.json", profile)
    print(json.dumps(profile, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    prepare(args.root)
