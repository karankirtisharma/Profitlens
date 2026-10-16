"""Explicitly publish the existing licensed FHDC pack to the hosted demo.

Only organization/owner membership provisioning uses SQL. Business records use
authenticated preview/confirm and PDF upload APIs. No AI calls or password resets.
"""

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import httpx
from dotenv import dotenv_values
from profitlens import database as db
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url

ROOT = Path("data/private/real-world-fhdc-2025")
ORG = "demo-fhdc-real"
NAME = "Real Data - FHDC Expenses (GBP)"
ORIGIN = "https://profitlens-six-psi.vercel.app"
OWNER = "karan@profitlens.local"


def checked(client, method, path, **kwargs):
    response = client.request(method, path, **kwargs)
    if response.is_error:
        raise RuntimeError(
            f"{method} {path}: HTTP {response.status_code}; no automatic retry"
        )
    return response


def fingerprint(conn):
    """Exclude session/rate counters, preserve every other workspace's business rows."""
    values = {}
    for table in db.metadata.sorted_tables:
        if "organization_id" in table.c:
            rows = conn.execute(
                select(table).where(table.c.organization_id != ORG)
            ).mappings()
            values[table.name] = sorted(
                json.dumps(dict(r), default=str, sort_keys=True) for r in rows
            )
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def run():
    cfg = dotenv_values(".env.cloud-admin")
    url = make_url(cfg["DATABASE_URL"])
    if (
        not url.host
        or not url.host.endswith(".neon.tech")
        or url.query.get("sslmode") not in {"require", "verify-full", "verify-ca"}
    ):
        raise RuntimeError("Expected the explicitly configured TLS Neon demo database")
    if cfg.get("WEB_ORIGIN") != ORIGIN:
        raise RuntimeError("Cloud configuration does not match the hosted frontend")
    for item in json.loads((ROOT / "manifest.json").read_text()):
        content = (ROOT / "originals" / item["file"]).read_bytes()
        if hashlib.sha256(content).hexdigest() != item["sha256"]:
            raise RuntimeError("Original source hash mismatch")
    prepared = ROOT / "prepared/real"
    rows = list(
        csv.DictReader(
            (prepared / "expenses.csv").open(encoding="utf-8-sig", newline="")
        )
    )
    if len(rows) != 141 or sum(
        (Decimal(r["amount"]) for r in rows), Decimal(0)
    ) != Decimal("28362.37"):
        raise RuntimeError(
            "Prepared expense pack differs from the verified source totals"
        )
    pdf = (prepared / "UNLINKED-contract-register.pdf").read_bytes()
    if pdf != (ROOT / "originals/contract-register-2026-08.pdf").read_bytes():
        raise RuntimeError("Register PDF differs from the original")

    engine = create_engine(
        url.set(drivername="postgresql+psycopg"), connect_args={"connect_timeout": 15}
    )
    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "workspace": ORG,
        "origin": ORIGIN,
        "ai_calls": 0,
        "checks": [],
    }
    with httpx.Client(
        base_url=ORIGIN, headers={"Origin": ORIGIN}, timeout=70
    ) as client:
        # Validate credentials before changing any database state. A lockout is not bypassed.
        checked(
            client,
            "POST",
            "/api/auth/login",
            json={"email": OWNER, "password": cfg["DEMO_PASSWORD"]},
        )
        try:
            with engine.begin() as conn:
                before = fingerprint(conn)
                owner = conn.execute(
                    select(db.users.c.id).where(db.users.c.email == OWNER)
                ).scalar_one()
                existing = (
                    conn.execute(
                        select(db.organizations).where(db.organizations.c.id == ORG)
                    )
                    .mappings()
                    .first()
                )
                if existing:
                    if existing["name"] != NAME or existing["currency"] != "GBP":
                        raise RuntimeError(
                            "Existing workspace differs; manual review required"
                        )
                    role = conn.execute(
                        select(db.memberships.c.role).where(
                            db.memberships.c.organization_id == ORG,
                            db.memberships.c.user_id == owner,
                        )
                    ).scalar_one_or_none()
                    if role != "admin":
                        raise RuntimeError(
                            "Existing membership differs; do not restore revoked access"
                        )
                else:
                    conn.execute(
                        db.organizations.insert().values(
                            id=ORG, name=NAME, currency="GBP"
                        )
                    )
                    conn.execute(
                        db.memberships.insert().values(
                            organization_id=ORG, user_id=owner, role="admin"
                        )
                    )
            base = f"/api/workspaces/{ORG}"
            account = checked(client, "GET", "/api/auth/me").json()
            assert ORG in {w["id"] for w in account["workspaces"]}
            for kind in ("customers", "expenses"):
                path = prepared / f"{kind}.csv"
                batch = checked(
                    client,
                    "POST",
                    base + f"/imports/{kind}/preview",
                    files={
                        "file": (
                            f"fhdc-public-{kind}.csv",
                            path.read_bytes(),
                            "text/csv",
                        )
                    },
                ).json()
                if batch["issues"] or batch["state"] not in {"ready", "confirmed"}:
                    raise RuntimeError("Preview needs review; existing data preserved")
                result = checked(
                    client, "POST", base + f"/imports/{batch['id']}/confirm"
                ).json()
                assert result["state"] == "confirmed"
                repeated = checked(
                    client, "POST", base + f"/imports/{batch['id']}/confirm"
                ).json()
                assert repeated["state"] == "confirmed"
                report["checks"].append(
                    {
                        "import": kind,
                        "rows": batch["row_count"],
                        "duplicate_confirmation": "passed",
                    }
                )
            doc = checked(
                client,
                "POST",
                base + "/contracts",
                data={"customer_id": "UNLINKED-PUBLIC-REGISTER"},
                files={
                    "file": ("UNLINKED-contract-register.pdf", pdf, "application/pdf")
                },
            ).json()
            assert doc["state"] == "unreviewed"
            stored = checked(
                client, "GET", base + f"/contracts/{doc['id']}/file"
            ).content
            assert hashlib.sha256(stored).digest() == hashlib.sha256(pdf).digest()
            loaded = {
                kind: checked(client, "GET", base + f"/records/{kind}").json()
                for kind in ("customers", "invoices", "expenses")
            }
            assert (
                len(loaded["customers"]) == 2
                and len(loaded["invoices"]) == 0
                and len(loaded["expenses"]) == 141
            )
            assert sum(
                (Decimal(r["amount"]) for r in loaded["expenses"]), Decimal(0)
            ) == Decimal("28362.37")
            item = checked(
                client,
                "GET",
                base + "/profitability",
                params={
                    "customer_id": "UNALLOCATED-PUBLIC-SPEND",
                    "billing_period": "2025-12",
                },
            ).json()["items"][0]
            assert (
                item["attributed_cost"] == "6035.77"
                and item["contribution"] is None
                and item["margin_percent"] is None
            )
            assert client.get(base + "/records/invoices/CLOUD-QA-I").status_code == 404
            report.update(
                counts={k: len(v) for k, v in loaded.items()},
                expense_total="28362.37",
                currency="GBP",
                pdf_hash_verified=True,
                contract_review_state="unreviewed",
                december_cost="6035.77",
                missing_profit_remains_null=True,
                cross_workspace_record_denied=True,
            )
            with engine.connect() as conn:
                assert fingerprint(conn) == before, (
                    "Other workspaces changed during import; review concurrent activity"
                )
            report["existing_workspaces_unchanged"] = True
        finally:
            client.post("/api/auth/logout")
            engine.dispose()
    with httpx.Client(base_url=ORIGIN, timeout=30) as anonymous:
        assert (
            anonymous.get(f"/api/workspaces/{ORG}/records/expenses").status_code == 401
        )
    report["anonymous_access_denied"] = True
    (ROOT / "hosted-publication.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish-hosted-demo", action="store_true", required=True)
    parser.parse_args()
    run()
