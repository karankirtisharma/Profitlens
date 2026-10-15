"""Authenticated API evaluation in the existing disposable test DB; AI is disabled."""

import csv
import hashlib
import io
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

from profitlens.config import settings
from sqlalchemy.engine import make_url

# Must happen before importing the app/database; never use the live business database.
url = make_url(settings.database_url).set(database="profitlens_test")
assert url.host in {"localhost", "127.0.0.1"} and url.database.endswith("_test")
settings.database_url = url.render_as_string(hide_password=False)
settings.ai_provider = "disabled"
settings.storage_dir = Path("data/private/real-world-fhdc-2025/api-uploads")
os.environ["AI_PROVIDER"] = "disabled"

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from profitlens import database as db  # noqa: E402
from profitlens.main import app  # noqa: E402
from profitlens.security import passwords  # noqa: E402
from sqlalchemy import select  # noqa: E402

ROOT = Path("data/private/real-world-fhdc-2025")
REAL = "qa-fhdc-real"
SYN = "qa-fhdc-synthetic-companion"
BUCKET = "UNALLOCATED-PUBLIC-SPEND"
LIBRARY = "UNLINKED-PUBLIC-REGISTER"
results = []


def check(label, condition, details=None):
    results.append(dict(test=label, passed=bool(condition), details=details))
    if not condition:
        raise AssertionError(label)


def save():
    (ROOT / "evaluation-results.json").write_text(
        json.dumps(
            dict(
                timestamp=datetime.now(timezone.utc).isoformat(),
                database="profitlens_test",
                workspaces=[REAL, SYN],
                ai_provider="disabled",
                tests=results,
                passed=sum(r["passed"] for r in results),
                failed=sum(not r["passed"] for r in results),
            ),
            indent=2,
        ),
        encoding="utf-8",
    )


def payload(fields, rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode()


def run():
    command.upgrade(Config("alembic.ini"), "head")
    # Administrative fixture provisioning only. Business data exclusively uses API routes.
    # The app has no workspace-creation HTTP route.
    credentials_file = ROOT / "qa-credentials.json"
    credentials = (
        json.loads(credentials_file.read_text())
        if credentials_file.exists()
        else {
            "email": "fhdc-qa-" + secrets.token_hex(6) + "@example.test",
            "password": secrets.token_urlsafe(32),
            "analyst_email": "fhdc-readonly-" + secrets.token_hex(6) + "@example.test",
            "analyst_password": secrets.token_urlsafe(32),
        }
    )
    with db.engine.begin() as conn:
        for org, title, currency in [
            (REAL, "PUBLIC DATA - unallocated FHDC spend (debits only)", "GBP"),
            (SYN, "SYNTHETIC companion - no relation to FHDC", "INR"),
        ]:
            existing = (
                conn.execute(
                    select(db.organizations).where(db.organizations.c.id == org)
                )
                .mappings()
                .first()
            )
            if existing:
                assert existing["name"] == title and existing["currency"] == currency
            else:
                conn.execute(
                    db.organizations.insert().values(
                        id=org, name=title, currency=currency
                    )
                )
        ids = {}
        for key, password_key, role, orgs in [
            ("email", "password", "admin", [REAL, SYN]),
            ("analyst_email", "analyst_password", "analyst", [REAL]),
        ]:
            uid = conn.execute(
                select(db.users.c.id).where(db.users.c.email == credentials[key])
            ).scalar_one_or_none()
            if not uid:
                uid = db.uid()
                conn.execute(
                    db.users.insert().values(
                        id=uid,
                        email=credentials[key],
                        name="Dataset QA " + role,
                        password_hash=passwords.hash(credentials[password_key]),
                    )
                )
                for org in orgs:
                    conn.execute(
                        db.memberships.insert().values(
                            organization_id=org, user_id=uid, role=role
                        )
                    )
            ids[role] = uid
    # Local ignored credentials allow resuming through the ordinary login form; never printed.
    credentials_file.write_text(json.dumps(credentials), encoding="utf-8")
    c = TestClient(app, headers={"Origin": settings.web_origin})
    check(
        "Unauthenticated records are denied",
        c.get(f"/api/workspaces/{REAL}/records/expenses").status_code == 401,
    )
    check(
        "Ordinary password login",
        c.post(
            "/api/auth/login",
            json={"email": credentials["email"], "password": credentials["password"]},
        ).status_code
        == 200,
    )

    def preview(org, kind, filename, content):
        r = c.post(
            f"/api/workspaces/{org}/imports/{kind}/preview",
            files={"file": (filename, content, "text/csv")},
        )
        check(
            f"Preview HTTP {org}/{filename}",
            r.status_code == 200,
            {"status": r.status_code},
        )
        return r.json()

    batches = {}
    for org, folder in [(REAL, "real"), (SYN, "synthetic-companion")]:
        for kind in ("customers", "invoices", "expenses"):
            path = ROOT / "prepared" / folder / f"{kind}.csv"
            if not path.exists():
                continue
            batch = preview(org, kind, path.name, path.read_bytes())
            check(
                f"Rows valid {org}/{kind}",
                batch["state"] in {"ready", "confirmed"} and not batch["issues"],
                {"rows": batch["row_count"], "issues": batch["issues"]},
            )
            r = c.post(f"/api/workspaces/{org}/imports/{batch['id']}/confirm")
            check(
                f"Confirmed {org}/{kind}",
                r.status_code == 200 and r.json()["state"] == "confirmed",
                r.json().get("result"),
            )
            batches[(org, kind)] = batch
    count_before = len(c.get(f"/api/workspaces/{REAL}/records/expenses").json())
    duplicate = preview(
        REAL,
        "expenses",
        "expenses.csv",
        (ROOT / "prepared/real/expenses.csv").read_bytes(),
    )
    check(
        "Same file retry is idempotent",
        duplicate["id"] == batches[(REAL, "expenses")]["id"]
        and duplicate["state"] == "confirmed",
    )
    c.post(f"/api/workspaces/{REAL}/imports/{duplicate['id']}/confirm")
    check(
        "Duplicate confirm adds no expenses",
        len(c.get(f"/api/workspaces/{REAL}/records/expenses").json()) == count_before,
    )
    # Test original excluded credit via unchanged signed amount. It must be rejected.
    exclusion = json.loads((ROOT / "excluded-records.json").read_text())[0]
    fields = list(exclusion["target"])
    rejected = preview(
        REAL,
        "expenses",
        "negative-original-credit.csv",
        payload(fields, [exclusion["target"]]),
    )
    check(
        "Signed source credit is rejected, not silently changed",
        rejected["state"] == "invalid",
        rejected["issues"],
    )
    check(
        "Invalid batch cannot be confirmed",
        c.post(f"/api/workspaces/{REAL}/imports/{rejected['id']}/confirm").status_code
        == 409,
    )
    with (ROOT / "prepared/real/expenses.csv").open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        sample = next(reader)
        fields = reader.fieldnames
    conflicting = sample | {"amount": "0.01"}
    r = preview(REAL, "expenses", "conflicting-id.csv", payload(fields, [conflicting]))
    check("Conflicting stable ID rejected", r["state"] == "invalid", r["issues"])
    missing = sample | {"expense_id": "QA-UNKNOWN", "customer_id": "DOES-NOT-EXIST"}
    r = preview(REAL, "expenses", "unknown-customer.csv", payload(fields, [missing]))
    check("Unlinked customer reference rejected", r["state"] == "invalid")
    with (ROOT / "prepared/synthetic-companion/invoices.csv").open(
        newline="", encoding="utf-8"
    ) as f:
        reader = csv.DictReader(f)
        invoice = next(reader) | {"invoice_id": "QA-BAD-TOTAL", "total": "0.01"}
        r = preview(
            SYN, "invoices", "invalid-total.csv", payload(reader.fieldnames, [invoice])
        )
    check("Invalid invoice arithmetic rejected", r["state"] == "invalid")
    profile = json.loads((ROOT / "profile.json").read_text())
    check(
        "All prepared real expenses persisted",
        count_before == profile["imported_expense_candidates"],
        count_before,
    )
    check(
        "Source printed totals independently reconcile",
        all(v["footer_reconciles"] for v in profile["file_profiles"]),
    )
    for period, expected in profile["expected_period_costs"].items():
        r = c.get(
            f"/api/workspaces/{REAL}/profitability",
            params={"customer_id": BUCKET, "billing_period": period},
        ).json()["items"][0]
        check(
            f"Real debit subset exact cost {period}",
            r["attributed_cost"] == expected,
            {"expected": expected, "actual": r["attributed_cost"]},
        )
        check(
            f"No fabricated revenue/profit {period}",
            r["net_billed_revenue"] is None
            and r["contribution"] is None
            and r["margin_percent"] is None
            and not r["findings"]
            and "missing_invoices" in {w["code"] for w in r["warnings"]},
        )
    records = c.get(f"/api/workspaces/{REAL}/records/expenses").json()
    logs = {
        v["target"]["expense_id"]: v
        for v in (
            json.loads(line)
            for line in (ROOT / "transformations.jsonl").read_text().splitlines()
        )
        if v["disposition"] == "included"
    }
    check(
        "All real records trace CSV row -> original PDF page/row/hash",
        all(
            r["source"]["row"] == logs[r["expense_id"]]["target_csv_row"]
            and r["source"]["sha256"]
            == hashlib.sha256(
                (ROOT / "prepared/real/expenses.csv").read_bytes()
            ).hexdigest()
            for r in records
        ),
    )
    contracts = {}
    for org, cid, path in [
        (REAL, LIBRARY, ROOT / "prepared/real/UNLINKED-contract-register.pdf")
    ] + [
        (SYN, cid, ROOT / f"prepared/synthetic-companion/{cid}-current.pdf")
        for cid in ("EVAL-01", "EVAL-06", "EVAL-11")
    ]:
        r = c.post(
            f"/api/workspaces/{org}/contracts",
            data={"customer_id": cid},
            files={"file": (path.name, path.read_bytes(), "application/pdf")},
        )
        check(
            f"PDF upload/extraction {cid}",
            r.status_code == 201,
            {"status": r.status_code},
        )
        record = r.json()
        contracts[cid] = record["id"]
        original = c.get(f"/api/workspaces/{org}/contracts/{record['id']}/file")
        check(
            f"Private PDF round trip hash {cid}",
            hashlib.sha256(original.content).digest()
            == hashlib.sha256(path.read_bytes()).digest(),
        )
        if org == SYN:
            terms = dict(
                effective_from="2026-04-01",
                effective_to="2026-09-30",
                currency="INR",
                billing_frequency="monthly",
                monthly_rate="1000.00",
                monthly_discount="0.00",
                source_page=1,
            )
            check(
                f"Review explicitly synthetic terms {cid}",
                c.put(
                    f"/api/workspaces/{SYN}/contracts/{record['id']}/terms", json=terms
                ).status_code
                == 200,
            )
        else:
            check(
                "Real register stays unreviewed and separate",
                record["state"] == "unreviewed" and record["customer_id"] == LIBRARY,
            )
    for cid in ("EVAL-01", "EVAL-06", "EVAL-11"):
        for period in ("2026-08", "2026-09"):
            item = c.get(
                f"/api/workspaces/{SYN}/profitability",
                params={"customer_id": cid, "billing_period": period},
            ).json()["items"][0]
            if item["attributed_cost"] is not None:
                r = c.put(
                    f"/api/workspaces/{SYN}/profitability/{cid}/{period}/cost-review",
                    json={
                        "input_hash": item["cost_input_hash"],
                        "note": "Synthetic fixture only: complete against supplied test expense ledger.",
                    },
                )
                check(
                    f"Synthetic cost completeness {cid}/{period}", r.status_code == 200
                )
    expected = {
        "EVAL-01": ("1200.00", "400.00", "800.00", "66.67", {"pricing_mismatch"}),
        "EVAL-06": (
            "1000.00",
            "800.00",
            "200.00",
            "20.00",
            {"cost_increase", "margin_decline"},
        ),
        "EVAL-11": ("1000.00", None, None, None, set()),
    }
    for cid, values in expected.items():
        item = c.get(
            f"/api/workspaces/{SYN}/profitability",
            params={"customer_id": cid, "billing_period": "2026-09"},
        ).json()["items"][0]
        observed = tuple(
            item[k]
            for k in (
                "net_billed_revenue",
                "attributed_cost",
                "contribution",
                "margin_percent",
            )
        )
        check(
            f"Independent synthetic arithmetic {cid}",
            observed == values[:4],
            {"expected": values[:4], "actual": observed},
        )
        check(
            f"Implemented discrepancy rules {cid}",
            {f["rule"] for f in item["findings"]} == values[4],
            [f["rule"] for f in item["findings"]],
        )
    # Read-only retrieval, no provider call. Register is reference context, never pricing truth.
    for org, cid, mode, query in [
        (REAL, LIBRARY, "baseline", "maintenance"),
        (SYN, "EVAL-01", "context", "payroll monthly delivery"),
    ]:
        r = c.get(
            f"/api/workspaces/{org}/evidence/search",
            params={
                "customer_id": cid,
                "billing_period": "2026-09",
                "q": query,
                "mode": mode,
            },
        )
        check(
            f"Retrieval HTTP {cid}",
            r.status_code == 200,
            {"status": r.status_code, "detail": r.json().get("detail")},
        )
        r = r.json()
        check(
            f"Local retrieval with source pages {cid}",
            bool(r["items"]) and all(p["source_url"] and p["page"] for p in r["items"]),
        )
    r = c.get(
        f"/api/workspaces/{REAL}/evidence/search",
        params={
            "customer_id": LIBRARY,
            "billing_period": "2026-09",
            "q": "maintenance",
            "mode": "context",
        },
    ).json()
    check("Unreviewed register excluded from pricing evidence", not r["items"])
    with db.engine.begin() as conn:
        if not conn.execute(
            select(db.grants).where(
                db.grants.c.organization_id == REAL,
                db.grants.c.user_id == ids["analyst"],
                db.grants.c.customer_id == BUCKET,
            )
        ).first():
            conn.execute(
                db.grants.insert().values(
                    organization_id=REAL, user_id=ids["analyst"], customer_id=BUCKET
                )
            )
    analyst = TestClient(app, headers={"Origin": settings.web_origin})
    check(
        "Analyst authenticates normally",
        analyst.post(
            "/api/auth/login",
            json={
                "email": credentials["analyst_email"],
                "password": credentials["analyst_password"],
            },
        ).status_code
        == 200,
    )
    check(
        "Analyst cannot import",
        analyst.post(
            f"/api/workspaces/{REAL}/imports/expenses/preview",
            files={
                "file": (
                    "expenses.csv",
                    (ROOT / "prepared/real/expenses.csv").read_bytes(),
                    "text/csv",
                )
            },
        ).status_code
        == 403,
    )
    check(
        "Other tenant is inaccessible",
        analyst.get(f"/api/workspaces/{SYN}/records/invoices").status_code == 404,
    )
    check(
        "Ungranted register PDF inaccessible",
        analyst.get(
            f"/api/workspaces/{REAL}/contracts/{contracts[LIBRARY]}/file"
        ).status_code
        == 404,
    )
    check(
        "No external AI configured in evaluation process",
        c.get(f"/api/workspaces/{REAL}/ai/status").json()["configured"] is False,
    )
    # Explicitly test refusal rather than invoking the configured development provider.
    r = c.post(
        f"/api/workspaces/{SYN}/investigations",
        json={
            "customer_id": "EVAL-01",
            "billing_period": "2026-09",
            "question": "What does the payroll monthly delivery contract show?",
        },
    )
    check(
        "Investigation records offline provider state",
        r.status_code == 201 and r.json()["result"]["status"] == "provider_unavailable",
        {
            "status_code": r.status_code,
            "status": r.json().get("result", {}).get("status"),
        },
    )
    c.post("/api/auth/logout")
    analyst.post("/api/auth/logout")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        results.append(
            dict(
                test="Evaluation completed without unexpected error",
                passed=False,
                details=type(exc).__name__,
            )
        )
        raise
    finally:
        save()
        print(
            json.dumps(
                {
                    "passed": sum(r["passed"] for r in results),
                    "failed": sum(not r["passed"] for r in results),
                    "report": str(ROOT / "evaluation-results.json"),
                }
            )
        )
