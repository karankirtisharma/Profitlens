"""Publish the prepared pack to two explicitly separate local demo workspaces.

Administrative identity provisioning is explicit; business data uses normal HTTP
login, preview/confirm and document APIs. Never calls an AI provider.
"""

import argparse
import csv
import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

import httpx
from profitlens import database as db
from profitlens.config import settings
from profitlens.security import passwords
from sqlalchemy import select
from sqlalchemy.engine import make_url

ROOT = Path("data/private/real-world-fhdc-2025")
REAL = "demo-fhdc-real"
SYN = "demo-fhdc-synthetic"
WORKSPACES = [
    (REAL, "Real Data - FHDC Expenses (GBP)", "GBP", "real"),
    (SYN, "Synthetic - Financial Demo (INR)", "INR", "synthetic-companion"),
]
OWNER = "karan@profitlens.local"


def request(client, method, path, **kwargs):
    response = client.request(method, path, **kwargs)
    if response.is_error:
        raise RuntimeError(f"{method} {path}: HTTP {response.status_code}")
    return response.json()


def outside_fingerprint(conn):
    """Compare all pre-existing business rows outside the two demo workspaces."""
    snapshot = {}
    for table in db.metadata.sorted_tables:
        if "organization_id" not in table.c:
            continue
        rows = conn.execute(
            select(table).where(table.c.organization_id.not_in([REAL, SYN]))
        ).mappings()
        snapshot[table.name] = sorted(
            json.dumps(dict(row), default=str, sort_keys=True) for row in rows
        )
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()


def extra_import_pack():
    """Unloaded synthetic case from the existing fixture, never renamed real data."""
    folder = ROOT / "prepared/synthetic-new-import"
    folder.mkdir(exist_ok=True)
    for kind in ("customers", "invoices", "expenses"):
        with Path(f"demo-files/evaluation/{kind}.csv").open(
            encoding="utf-8-sig", newline=""
        ) as source:
            reader = csv.DictReader(source)
            rows = [
                row
                for row in reader
                if row["customer_id"] == "EVAL-02"
                and (
                    kind == "customers"
                    or row["billing_period"] in {"2026-08", "2026-09"}
                )
            ]
            with (folder / f"{kind}.csv").open(
                "w", encoding="utf-8", newline=""
            ) as output:
                writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
                writer.writeheader()
                writer.writerows(rows)
    (folder / "EVAL-02-current.pdf").write_bytes(
        Path("demo-files/evaluation/EVAL-02-current.pdf").read_bytes()
    )


def run():
    url = make_url(settings.database_url)
    if url.host not in {"127.0.0.1", "localhost"} or url.database != "profitlens":
        raise SystemExit(
            "This explicit demo publisher requires local database profitlens."
        )
    if not (ROOT / "profile.json").exists():
        raise SystemExit("Run fhdc_prepare.py first.")
    credentials_path = ROOT / "dashboard-demo-credentials.json"
    credentials = (
        json.loads(credentials_path.read_text())
        if credentials_path.exists()
        else {
            "email": f"dataset-demo-{secrets.token_hex(6)}@example.test",
            "password": secrets.token_urlsafe(32),
        }
    )
    # Save before provisioning so a failed/interrupted run can safely resume.
    credentials_path.write_text(json.dumps(credentials), encoding="utf-8")
    with db.engine.begin() as conn:
        before = outside_fingerprint(conn)
        owner = conn.execute(
            select(db.users.c.id).where(db.users.c.email == OWNER)
        ).scalar_one()
        operator = conn.execute(
            select(db.users.c.id).where(db.users.c.email == credentials["email"])
        ).scalar_one_or_none()
        if not operator:
            operator = db.uid()
            conn.execute(
                db.users.insert().values(
                    id=operator,
                    email=credentials["email"],
                    name="Dataset demo importer",
                    password_hash=passwords.hash(credentials["password"]),
                )
            )
        for org, name, currency, _ in WORKSPACES:
            existing = (
                conn.execute(
                    select(db.organizations).where(db.organizations.c.id == org)
                )
                .mappings()
                .first()
            )
            if existing:
                if existing["name"] != name or existing["currency"] != currency:
                    raise RuntimeError(
                        "Existing demo workspace metadata differs; review manually."
                    )
                # Do not silently restore revoked access on a later rerun.
                for uid in (owner, operator):
                    role = conn.execute(
                        select(db.memberships.c.role).where(
                            db.memberships.c.organization_id == org,
                            db.memberships.c.user_id == uid,
                        )
                    ).scalar_one_or_none()
                    if role != "admin":
                        raise RuntimeError(
                            "Demo membership changed; review access manually."
                        )
            else:
                conn.execute(
                    db.organizations.insert().values(
                        id=org, name=name, currency=currency
                    )
                )
                for uid in (owner, operator):
                    conn.execute(
                        db.memberships.insert().values(
                            organization_id=org, user_id=uid, role="admin"
                        )
                    )

    checks = []
    with httpx.Client(
        base_url="http://127.0.0.1:8000",
        headers={"Origin": settings.web_origin},
        timeout=60,
    ) as client:
        request(client, "POST", "/api/auth/login", json=credentials)
        try:
            account = request(client, "GET", "/api/auth/me")
            assert {w["id"] for w in account["workspaces"]} == {REAL, SYN}
            for org, _, _, folder in WORKSPACES:
                base = f"/api/workspaces/{org}"
                for kind in ("customers", "invoices", "expenses"):
                    path = ROOT / "prepared" / folder / f"{kind}.csv"
                    if not path.exists():
                        continue
                    batch = request(
                        client,
                        "POST",
                        base + f"/imports/{kind}/preview",
                        files={"file": (path.name, path.read_bytes(), "text/csv")},
                    )
                    if batch["issues"] or batch["state"] not in {"ready", "confirmed"}:
                        raise RuntimeError(
                            f"{org}/{kind}: preview conflicts; existing edits preserved."
                        )
                    confirmed = request(
                        client, "POST", base + f"/imports/{batch['id']}/confirm"
                    )
                    assert confirmed["state"] == "confirmed"
                    checks.append(
                        {
                            "workspace": org,
                            "kind": kind,
                            "rows": batch["row_count"],
                            "result": confirmed["result"],
                        }
                    )
                pdfs = (
                    [("UNLINKED-PUBLIC-REGISTER", "UNLINKED-contract-register.pdf")]
                    if org == REAL
                    else [
                        (cid, f"{cid}-current.pdf")
                        for cid in ("EVAL-01", "EVAL-06", "EVAL-11")
                    ]
                )
                for cid, name in pdfs:
                    path = ROOT / "prepared" / folder / name
                    document = request(
                        client,
                        "POST",
                        base + "/contracts",
                        data={"customer_id": cid},
                        files={"file": (name, path.read_bytes(), "application/pdf")},
                    )
                    if org == SYN and document["state"] == "unreviewed":
                        request(
                            client,
                            "PUT",
                            base + f"/contracts/{document['id']}/terms",
                            json={
                                "effective_from": "2026-04-01",
                                "effective_to": "2026-09-30",
                                "currency": "INR",
                                "billing_frequency": "monthly",
                                "monthly_rate": "1000.00",
                                "monthly_discount": "0.00",
                                "source_page": 1,
                            },
                        )
                    if org == REAL:
                        assert document["state"] == "unreviewed", (
                            "Real register must remain unreviewed"
                        )
                if org == SYN:
                    for cid in ("EVAL-01", "EVAL-06", "EVAL-11"):
                        for month in ("2026-08", "2026-09"):
                            item = request(
                                client,
                                "GET",
                                base + "/profitability",
                                params={"customer_id": cid, "billing_period": month},
                            )["items"][0]
                            if (
                                item["attributed_cost"] is not None
                                and item["profitability_status"] != "confirmed"
                            ):
                                request(
                                    client,
                                    "PUT",
                                    base + f"/profitability/{cid}/{month}/cost-review",
                                    json={
                                        "input_hash": item["cost_input_hash"],
                                        "note": "Synthetic companion only: fixture expense ledger verified complete. No relation to real FHDC data.",
                                    },
                                )
                counts = {
                    kind: len(request(client, "GET", base + f"/records/{kind}"))
                    for kind in ("customers", "invoices", "expenses")
                }
                counts["contracts"] = len(request(client, "GET", base + "/contracts"))
                checks.append({"workspace": org, "counts": counts})
            # Real data stays financially incomplete; synthetic findings remain demonstrable.
            real = request(
                client,
                "GET",
                f"/api/workspaces/{REAL}/profitability",
                params={
                    "customer_id": "UNALLOCATED-PUBLIC-SPEND",
                    "billing_period": "2025-12",
                },
            )["items"][0]
            assert real["attributed_cost"] == "6035.77" and real["contribution"] is None
            for cid, contribution, findings in [
                ("EVAL-01", "800.00", {"pricing_mismatch"}),
                ("EVAL-06", "200.00", {"cost_increase", "margin_decline"}),
                ("EVAL-11", None, set()),
            ]:
                item = request(
                    client,
                    "GET",
                    f"/api/workspaces/{SYN}/profitability",
                    params={"customer_id": cid, "billing_period": "2026-09"},
                )["items"][0]
                assert item["contribution"] == contribution
                assert {f["rule"] for f in item["findings"]} == findings
            assert (
                client.get("/api/workspaces/demo-org/records/invoices").status_code
                == 404
            )
        finally:
            client.post("/api/auth/logout")
    with db.engine.connect() as conn:
        assert outside_fingerprint(conn) == before, (
            "Existing workspaces changed during run; review activity."
        )
    extra_import_pack()
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "profitlens",
        "owner": OWNER,
        "checks": checks,
        "existing_workspaces_unchanged": True,
        "ai_calls": 0,
        "extra_import_pack": "prepared/synthetic-new-import (not preloaded)",
    }
    (ROOT / "dashboard-publication.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish-local-demo", action="store_true", required=True)
    parser.parse_args()
    run()
