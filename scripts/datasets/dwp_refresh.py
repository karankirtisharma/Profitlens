"""Download bounded original government CSVs and a reproducible source-linked subset."""

import csv
import hashlib
import io
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import httpx

ROOT = Path("data/private/dwp-2026")
URLS = {
    "2026-07": "https://assets.publishing.service.gov.uk/media/6ae32d6882273a0adc7b82ed/dwp-spending-over-_25000-july-2026.csv",
    "2026-08": "https://assets.publishing.service.gov.uk/media/6ae34d9983b993d8d93eb778/dwp-spending-over-_25000-august-2026.csv",
    "2026-09": "https://assets.publishing.service.gov.uk/media/6ae34e81a5c2f99e3a7b832f/dwp-spending-over-_25000-september-2026.csv",
}


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest = []
    selected = []
    reserved = []
    for month, url in URLS.items():
        path = ROOT / (month + ".csv")
        if not path.exists():
            data = bytearray()
            with httpx.stream("GET", url, timeout=60) as response:
                response.raise_for_status()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > 3_000_000:
                        raise RuntimeError("Download exceeded 3 MB bound")
            path.write_bytes(data)
        raw = path.read_bytes()
        text = raw.decode("cp1252")
        rows = list(csv.DictReader(io.StringIO(text)))
        # A bounded first-200-row selection per release, not a company-wide total.
        for number, r in enumerate(rows[:220], 2):
            value = Decimal(
                r["Transparency Invoice Amount"]
                .replace("£", "")
                .replace(",", "")
                .strip()
            )
            (selected if number < 202 else reserved).append(
                r
                | {
                    "Amount": str(value),
                    "Date": datetime.strptime(r["Invoice Paid Date"], "%d/%m/%Y")
                    .date()
                    .isoformat(),
                    "Original row": str(number),
                    "Original URL": url,
                    "Release month": month,
                }
            )
        manifest.append(
            {
                "file": path.name,
                "url": url,
                "licence": "Open Government Licence v3.0",
                "licence_url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                "downloaded_at": datetime.now(UTC).isoformat(),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "rows": len(rows),
                "columns": list(rows[0]),
            }
        )
        print(
            json.dumps(
                {
                    "month": month,
                    "rows": len(rows),
                    "columns": list(rows[0]),
                    "example": rows[0],
                }
            )
        )
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    for name, records in [("demo-subset.csv", selected), ("new-import.csv", reserved)]:
        path = ROOT / name
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    (ROOT / "ground-truth.json").write_text(
        json.dumps(
            {
                "records": len(selected),
                "amount": str(sum(Decimal(r["Amount"]) for r in selected)),
                "per_month": {
                    m: str(
                        sum(
                            Decimal(r["Amount"])
                            for r in selected
                            if r["Release month"] == m
                        )
                    )
                    for m in URLS
                },
                "selection": "First 200 rows of each monthly release; source order, not representative of all spending",
                "transforms": [
                    "cp1252 to UTF-8",
                    "GBP symbol and thousands separators removed in additional Amount field",
                    "dd/mm/yyyy to ISO Date field",
                    "all original columns retained",
                    "original URL and row number added",
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
