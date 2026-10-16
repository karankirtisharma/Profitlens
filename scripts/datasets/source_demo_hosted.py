"""Prepare/publish two separated licensed source demos. Never sends records to AI."""

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import httpx
from dotenv import dotenv_values
from openpyxl import Workbook
from profitlens import database as db
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url

UCI = Path("data/private/uci-online-retail")
FHDC = Path("data/private/real-world-fhdc-2025")
ORIGIN = "https://profitlens-six-psi.vercel.app"
ORGS = {
    "demo-uci-real": "Real Data - UCI Sales (GBP)",
    "demo-fhdc-source": "Real Data - Council Expenditure (GBP)",
}


def checked(client, method, path, **kwargs):
    r = client.request(method, path, **kwargs)
    if r.is_error:
        raise RuntimeError(f"{method} {path}: HTTP {r.status_code}; no automatic retry")
    return r


def prepare():
    manifest = json.loads((UCI / "manifest.json").read_text())
    assert (
        hashlib.sha256((UCI / "online-retail.zip").read_bytes()).hexdigest()
        == manifest["sha256"]
    )
    for item in json.loads((FHDC / "manifest.json").read_text()):
        assert (
            hashlib.sha256((FHDC / "originals" / item["file"]).read_bytes()).hexdigest()
            == item["sha256"]
        )
    initial = {
        r["invoice_id"]
        for r in csv.DictReader((UCI / "prepared/invoices.csv").open(encoding="utf8"))
    }
    rows = list(
        csv.DictReader((UCI / "source-linked-sales-sample.csv").open(encoding="utf8"))
    )
    for filename, selected in (
        ("source-subset.xlsx", [r for r in rows if r["InvoiceNo"] in initial]),
        ("new-source-import.xlsx", [r for r in rows if r["InvoiceNo"] not in initial]),
    ):
        path = UCI / "prepared" / filename
        # Stable file bytes on reruns; avoid making equivalent workbooks with different ZIP timestamps.
        if not path.exists():
            book = Workbook()
            book.active.append(list(selected[0]))
            for row in selected:
                book.active.append(list(row.values()))
            book.save(path)
    selected = [r for r in rows if r["InvoiceNo"] in initial]
    return {
        "rows": len(selected),
        "amount": str(
            sum(
                (
                    (Decimal(r["Quantity"]) * Decimal(r["UnitPrice"])).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    for r in selected
                ),
                Decimal(0),
            )
        ),
    }


def snapshot(conn):
    out = {}
    for t in db.metadata.sorted_tables:
        if "organization_id" in t.c:
            out[t.name] = sorted(
                json.dumps(dict(r), sort_keys=True, default=str)
                for r in conn.execute(
                    select(t).where(t.c.organization_id.not_in(ORGS))
                ).mappings()
            )
    return hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()


def publish():
    expected = prepare()
    cfg = dotenv_values(".env.cloud-admin")
    url = make_url(cfg["DATABASE_URL"])
    assert url.host.endswith(".neon.tech") and url.query.get("sslmode") in {
        "require",
        "verify-full",
        "verify-ca",
    }
    assert cfg["WEB_ORIGIN"] == ORIGIN
    engine = create_engine(
        url.set(drivername="postgresql+psycopg"), connect_args={"connect_timeout": 15}
    )
    reports = {
        "timestamp": datetime.now(UTC).isoformat(),
        "ai_calls": 0,
        "workspaces": {},
    }
    with httpx.Client(base_url=ORIGIN, headers={"Origin": ORIGIN}, timeout=150) as c:
        checked(
            c,
            "POST",
            "/api/auth/login",
            json={"email": "karan@profitlens.local", "password": cfg["DEMO_PASSWORD"]},
        )
        try:
            with engine.begin() as conn:
                before = snapshot(conn)
                owner = conn.scalar(
                    select(db.users.c.id).where(
                        db.users.c.email == "karan@profitlens.local"
                    )
                )
                for org, name in ORGS.items():
                    old = (
                        conn.execute(
                            select(db.organizations).where(db.organizations.c.id == org)
                        )
                        .mappings()
                        .first()
                    )
                    if old:
                        assert old["name"] == name and old["currency"] == "GBP"
                        assert (
                            conn.scalar(
                                select(db.memberships.c.role).where(
                                    db.memberships.c.organization_id == org,
                                    db.memberships.c.user_id == owner,
                                )
                            )
                            == "admin"
                        )
                    else:
                        conn.execute(
                            db.organizations.insert().values(
                                id=org, name=name, currency="GBP"
                            )
                        )
                        conn.execute(
                            db.memberships.insert().values(
                                organization_id=org, user_id=owner, role="admin"
                            )
                        )
            base = "/api/workspaces/demo-uci-real"
            batch = checked(
                c,
                "POST",
                base + "/imports/customers/preview",
                files={
                    "file": (
                        "uci-customers.csv",
                        (UCI / "prepared/customers.csv").read_bytes(),
                    )
                },
            ).json()
            assert not batch["issues"]
            checked(c, "POST", base + f"/imports/{batch['id']}/confirm")
            mapping = {
                "kind": "reported_sales",
                "amount_mode": "quantity_price",
                "columns": {
                    "quantity": "Quantity",
                    "unit_price": "UnitPrice",
                    "date": "InvoiceDate",
                    "description": "Description",
                    "counterparty": "CustomerID",
                    "customer_id": "CustomerID",
                },
                "currency": "GBP",
                "profile_name": "UCI source sales",
            }
            plans = [
                (
                    "demo-uci-real",
                    UCI / "prepared/source-subset.xlsx",
                    "generic",
                    mapping,
                )
            ]
            for path in sorted((FHDC / "originals").glob("procurement-*.csv")):
                plans.append(
                    (
                        "demo-fhdc-source",
                        path,
                        "fhdc_card",
                        {
                            "kind": "expenditure",
                            "columns": {
                                "amount": "net_amount",
                                "date": "transaction_date",
                                "description": "description",
                                "counterparty": "supplier",
                            },
                            "currency": "GBP",
                            "date_format": "DMY",
                            "profile_name": "FHDC procurement card",
                        },
                    )
                )
            for org, path, adapter, config in plans:
                base = f"/api/workspaces/{org}"
                content = path.read_bytes()
                d = checked(
                    c,
                    "POST",
                    base + "/sources",
                    data={"adapter": adapter},
                    files={"file": (path.name, content)},
                ).json()
                if d["state"] != "confirmed":
                    p = checked(
                        c, "POST", base + f"/sources/{d['id']}/preview", json=config
                    ).json()
                    assert not p["issues"], "Source preview needs review"
                    for _ in range(2):
                        checked(
                            c,
                            "POST",
                            base + f"/sources/{d['id']}/confirm",
                            json={"preview_token": p["preview_token"]},
                        )
                assert (
                    checked(c, "GET", base + f"/sources/{d['id']}/file").content
                    == content
                )
                assert (
                    checked(
                        c,
                        "POST",
                        base + "/sources",
                        data={"adapter": adapter},
                        files={"file": (path.name, content)},
                    ).json()["id"]
                    == d["id"]
                )
            for org in ORGS:
                base = f"/api/workspaces/{org}"
                result = checked(c, "GET", base + "/facts").json()
                count, amount = (
                    (expected["rows"], expected["amount"])
                    if org == "demo-uci-real"
                    else (142, "27823.37")
                )
                assert (
                    result["total"] == count and result["groups"][0]["amount"] == amount
                )
                assert result["unmatched"] == (0 if org == "demo-uci-real" else 142)
                record = result["rows"][0]
                detail = checked(c, "GET", base + f"/facts/{record['id']}").json()
                assert detail["raw"] and detail["sha256"] and detail["mapping"]
                assert (
                    c.get(f"/api/workspaces/other-org/facts/{record['id']}").status_code
                    == 404
                )
                with httpx.Client(base_url=ORIGIN, timeout=30) as anon:
                    assert anon.get(base + "/facts").status_code == 401
                reports["workspaces"][org] = {
                    "rows": count,
                    "amount": amount,
                    "months": result["months"],
                    "checks": [
                        "normal login, extraction, preview, confirmation",
                        "exact total",
                        "original download byte equality",
                        "duplicate upload and confirmation",
                        "source row drill-down",
                        "unmatched semantics",
                        "anonymous/cross-tenant denial",
                    ],
                }
            with engine.connect() as conn:
                assert snapshot(conn) == before, "Other workspaces changed"
            reports["other_workspaces_unchanged"] = True
            (UCI / "source-hosted-publication.json").write_text(
                json.dumps(reports, indent=2), encoding="utf8"
            )
            print(json.dumps(reports, indent=2))
        finally:
            c.post("/api/auth/logout")
    engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if args.publish:
        publish()
    else:
        print(json.dumps(prepare()))
