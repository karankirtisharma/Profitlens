"""Real PostgreSQL integration tests. Requires a dedicated database ending in _test."""

import io
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from profitlens import database as db
from profitlens.config import settings
from profitlens.main import app
from profitlens.security import passwords
from reportlab.pdfgen import canvas
from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

TEST_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not TEST_URL,
    reason="Set TEST_DATABASE_URL to a dedicated PostgreSQL _test database",
)
PASSWORD = "test-only-long-passphrase"


@pytest.fixture(scope="module", autouse=True)
def migrated_database():
    if not TEST_URL:
        return
    url = make_url(TEST_URL)
    assert url.drivername.startswith("postgresql") and url.database.endswith("_test"), (
        "Tests require a dedicated _test PostgreSQL database"
    )
    original = db.engine
    db.engine = create_engine(TEST_URL, pool_pre_ping=True)
    command.upgrade(Config("alembic.ini"), "head")
    yield
    db.engine.dispose()
    db.engine = original


@pytest.fixture(scope="module")
def hash_password():
    return passwords.hash(PASSWORD)


@pytest.fixture(autouse=True)
def fixture_data(tmp_path, hash_password):
    old = settings.storage_dir
    settings.storage_dir = tmp_path
    with db.engine.begin() as conn:
        for table in reversed(db.metadata.sorted_tables):
            conn.execute(delete(table))
        conn.execute(
            db.organizations.insert(),
            [
                {"id": "a", "name": "Organization A", "currency": "INR"},
                {"id": "b", "name": "Organization B", "currency": "INR"},
            ],
        )
        for uid, org, role in [
            ("admin", "a", "admin"),
            ("finance", "a", "finance"),
            ("analyst", "a", "analyst"),
            ("outsider", "b", "admin"),
        ]:
            conn.execute(
                db.users.insert().values(
                    id=uid,
                    email=f"{uid}@example.test",
                    name=uid,
                    password_hash=hash_password,
                )
            )
            conn.execute(
                db.memberships.insert().values(
                    organization_id=org, user_id=uid, role=role
                )
            )
        conn.execute(
            db.customers.insert(),
            [
                {
                    "organization_id": "a",
                    "customer_id": "C1",
                    "name": "Allowed customer",
                    "industry": "Services",
                },
                {
                    "organization_id": "a",
                    "customer_id": "C2",
                    "name": "Restricted customer",
                    "industry": "Services",
                },
                {
                    "organization_id": "b",
                    "customer_id": "B1",
                    "name": "Other tenant",
                    "industry": "Services",
                },
            ],
        )
        conn.execute(
            db.grants.insert().values(
                organization_id="a", user_id="analyst", customer_id="C1"
            )
        )
    yield
    settings.storage_dir = old


def client(user="admin"):
    c = TestClient(app, headers={"Origin": settings.web_origin})
    response = c.post(
        "/api/auth/login", json={"email": f"{user}@example.test", "password": PASSWORD}
    )
    assert response.status_code == 200, response.text
    return c


BASE = "/api/workspaces/a"


def invoice(id="I1", customer="C1", **overrides):
    return (
        dict(
            invoice_id=id,
            customer_id=customer,
            billing_period="2026-09",
            currency="INR",
            subtotal="100.00",
            discount="10.00",
            tax="9.00",
            refund="0.00",
            total="99.00",
        )
        | overrides
    )


def csv(kind, rows):
    from profitlens.ingestion.csv_import import SCHEMAS

    columns = SCHEMAS[kind][1]
    return (
        ",".join(columns)
        + "\n"
        + "\n".join(",".join(str(r[k]) for k in columns) for r in rows)
        + "\n"
    ).encode()


def preview(c, kind, rows):
    r = c.post(
        BASE + f"/imports/{kind}/preview",
        files={"file": ("fixture.csv", csv(kind, rows), "text/csv")},
    )
    assert r.status_code == 200, r.text
    return r.json()


def pdf(text="Synthetic monthly contract: INR 100.00, September 2026."):
    output = io.BytesIO()
    p = canvas.Canvas(output)
    p.drawString(50, 750, text)
    p.save()
    return output.getvalue()


def upload(c, customer="C1", content=None):
    r = c.post(
        BASE + "/contracts",
        data={"customer_id": customer},
        files={"file": ("contract.pdf", content or pdf(), "application/pdf")},
    )
    assert r.status_code == 201, r.text
    return r.json()


TERMS = {
    "effective_from": "2026-09-01",
    "effective_to": "2027-02-28",
    "currency": "INR",
    "monthly_rate": "100.00",
    "monthly_discount": "0.00",
    "source_page": 1,
}


def test_fresh_migration_and_health():
    assert TestClient(app).get("/api/health").json()["database"] == "postgresql"
    with db.engine.connect() as conn:
        assert conn.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()


def test_auth_cookie_logout_expiry_and_no_secret_leak():
    c = client()
    me = c.get("/api/auth/me")
    assert me.status_code == 200 and "password" not in me.text
    assert (
        "httponly"
        in c.post(
            "/api/auth/login",
            json={"email": "admin@example.test", "password": PASSWORD},
        )
        .headers["set-cookie"]
        .lower()
    )
    assert c.post("/api/auth/logout").status_code == 200
    assert c.get("/api/auth/me").status_code == 401
    c = client()
    with db.engine.begin() as conn:
        conn.execute(
            db.sessions.update().values(expires_at=db.now() - timedelta(seconds=1))
        )
    assert c.get("/api/auth/me").status_code == 401


def test_csrf_and_failed_login_throttle():
    c = TestClient(app)
    assert (
        c.post(
            "/api/auth/login",
            json={"email": "admin@example.test", "password": PASSWORD},
        ).status_code
        == 403
    )
    c.headers["Origin"] = settings.web_origin
    for _ in range(5):
        assert (
            c.post(
                "/api/auth/login",
                json={"email": "unknown@example.test", "password": "incorrect"},
            ).status_code
            == 401
        )
    assert (
        c.post(
            "/api/auth/login",
            json={"email": "unknown@example.test", "password": "incorrect"},
        ).status_code
        == 429
    )


def test_tenant_and_customer_scope_for_reads_and_writes():
    outsider = client("outsider")
    for suffix in ["/records/customers", "/imports", "/contracts", "/members"]:
        assert outsider.get(BASE + suffix).status_code == 404
    analyst = client("analyst")
    assert [
        r["customer_id"] for r in analyst.get(BASE + "/records/customers").json()
    ] == ["C1"]
    assert analyst.get(BASE + "/records/customers/C2").status_code == 404
    assert analyst.get(BASE + "/imports").status_code == 403
    for endpoint in ["/records/invoices", "/records/expenses", "/records/customers"]:
        assert analyst.post(BASE + endpoint, json={}).status_code in (403, 422)
    assert analyst.post(BASE + "/records/invoices", json=invoice()).status_code == 403
    assert (
        client()
        .post(BASE + "/records/invoices", json=invoice(customer="B1"))
        .status_code
        == 404
    )


def test_manual_create_update_validation_and_audit():
    c = client("finance")
    assert (
        c.post(BASE + "/records/invoices", json=invoice(total="98")).status_code == 422
    )
    assert (
        c.post(BASE + "/records/invoices", json=invoice(currency="USD")).status_code
        == 422
    )
    assert (
        c.post(
            BASE + "/records/invoices", json=invoice() | {"organization_id": "b"}
        ).status_code
        == 422
    )
    assert c.post(BASE + "/records/invoices", json=invoice()).status_code == 201
    assert c.post(BASE + "/records/invoices", json=invoice()).status_code == 409
    assert (
        c.put(BASE + "/records/invoices/I1", json=invoice(id="I2")).status_code == 422
    )
    assert (
        c.put(
            BASE + "/records/invoices/I1", json=invoice(discount="0", total="109")
        ).status_code
        == 200
    )
    with db.engine.connect() as conn:
        assert len(conn.execute(select(db.audit)).all()) == 2


def test_invalid_import_does_not_commit_any_rows():
    c = client()
    batch = preview(c, "invoices", [invoice(), invoice(id="BAD", total="88")])
    assert batch["state"] == "invalid" and batch["issues"][0]["source_row"] == 3
    assert c.post(BASE + f"/imports/{batch['id']}/confirm").status_code == 409
    assert c.get(BASE + "/records/invoices").json() == []


def test_import_retry_provenance_and_identical_duplicate():
    c = client()
    batch = preview(c, "invoices", [invoice()])
    for _ in range(2):
        result = c.post(BASE + f"/imports/{batch['id']}/confirm")
        assert result.status_code == 200, result.text
        assert result.json()["result"] == {"inserted": 1, "skipped": 0}
    assert preview(c, "invoices", [invoice()])["id"] == batch["id"]
    other = c.post(
        BASE + "/imports/invoices/preview",
        files={"file": ("again.csv", csv("invoices", [invoice()]) + b"\n", "text/csv")},
    ).json()
    assert (
        c.post(BASE + f"/imports/{other['id']}/confirm").json()["result"]["skipped"]
        == 1
    )
    rows = c.get(BASE + "/records/invoices").json()
    assert len(rows) == 1
    assert (
        rows[0]["source"]["row"] == 2 and rows[0]["source"]["batch_id"] == batch["id"]
    )
    assert (
        c.put(
            BASE + "/records/invoices/I1", json=invoice(discount="0", total="109")
        ).status_code
        == 200
    )
    assert (
        c.get(BASE + "/records/invoices/I1").json()["source"]["batch_id"] == batch["id"]
    )


def test_confirmation_rechecks_changed_data_atomically():
    c = client()
    batch = preview(c, "invoices", [invoice(id="NEW"), invoice(id="RACE")])
    assert (
        c.post(
            BASE + "/records/invoices",
            json=invoice(id="RACE", discount="0", total="109"),
        ).status_code
        == 201
    )
    assert c.post(BASE + f"/imports/{batch['id']}/confirm").status_code == 409
    assert c.get(BASE + "/records/invoices/NEW").status_code == 404


def test_concurrent_confirmation_is_idempotent():
    c1, c2 = client(), client()
    batch = preview(c1, "invoices", [invoice()])
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda c: c.post(BASE + f"/imports/{batch['id']}/confirm"), [c1, c2]
            )
        )
    assert [r.status_code for r in responses] == [200, 200]
    assert len(c1.get(BASE + "/records/invoices").json()) == 1


@pytest.mark.parametrize(
    "rows",
    [[invoice(), invoice()], [invoice(customer="UNKNOWN")], [invoice(currency="USD")]],
)
def test_duplicate_unknown_and_currency_import_rejected(rows):
    assert preview(client(), "invoices", rows)["state"] == "invalid"


def test_csv_customer_then_expense_flow_and_scope():
    c = client()
    batch = preview(
        c,
        "customers",
        [{"customer_id": "C3", "name": "New customer", "industry": "Tech"}],
    )
    assert c.post(BASE + f"/imports/{batch['id']}/confirm").status_code == 200
    b = preview(
        c,
        "expenses",
        [
            {
                "expense_id": "E1",
                "customer_id": "C3",
                "billing_period": "2026-09",
                "category": "Hosting",
                "amount": "25.50",
                "currency": "INR",
            }
        ],
    )
    assert c.post(BASE + f"/imports/{b['id']}/confirm").status_code == 200
    assert len(c.get(BASE + "/records/expenses?customer_id=C3").json()) == 1
    assert client("analyst").get(BASE + "/records/expenses").json() == []


def test_pdf_privacy_review_and_revocation():
    c = client()
    content = pdf()
    doc = upload(c, content=content)
    assert doc["state"] == "unreviewed" and "file_key" not in doc
    assert upload(c, content=content)["id"] == doc["id"]
    path = BASE + f"/contracts/{doc['id']}"
    assert client("outsider").get(path + "/file").status_code == 404
    a = client("analyst")
    assert a.get(path + "/file").content.startswith(b"%PDF-")
    assert a.put(path + "/terms", json=TERMS).status_code == 403
    reviewed = c.put(path + "/terms", json=TERMS)
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["reviewed_by"] == "admin"
    assert (
        c.put(
            BASE + "/members/analyst/customers", json={"customer_ids": []}
        ).status_code
        == 200
    )
    assert (
        a.get(path + "/file").status_code == 404
        and a.get(BASE + "/contracts").json() == []
    )


def test_invalid_terms_overlap_and_unassigned_pdf():
    c = client()
    doc = upload(c)
    path = BASE + f"/contracts/{doc['id']}/terms"
    for change in [
        {"effective_to": "2026-01-01"},
        {"source_page": 2},
        {"monthly_discount": "101"},
        {"currency": "USD"},
    ]:
        assert c.put(path, json=TERMS | change).status_code == 422
    assert c.put(path, json=TERMS).status_code == 200
    other = upload(c, content=pdf("Another agreement with overlapping dates"))
    assert (
        c.put(BASE + f"/contracts/{other['id']}/terms", json=TERMS).status_code == 409
    )
    private = upload(c, customer="C2")
    assert (
        client("analyst").get(BASE + f"/contracts/{private['id']}/file").status_code
        == 404
    )


def test_invalid_pdf_and_oversize_csv_leave_no_business_data():
    c = client()
    assert (
        c.post(
            BASE + "/contracts",
            data={"customer_id": "C1"},
            files={"file": ("bad.pdf", b"not a PDF")},
        ).status_code
        == 422
    )
    assert c.get(BASE + "/contracts").json() == []
    assert not list(settings.storage_dir.rglob("*.pdf"))
    assert (
        c.post(
            BASE + "/imports/customers/preview",
            files={"file": ("large.csv", b"x" * (5 * 1024 * 1024 + 1))},
        ).status_code
        == 413
    )


def test_composite_database_foreign_key_prevents_cross_tenant_link():
    with pytest.raises(IntegrityError):
        with db.engine.begin() as conn:
            conn.execute(
                db.expenses.insert().values(
                    organization_id="a",
                    expense_id="E1",
                    customer_id="B1",
                    billing_period="2026-09",
                    category="Invalid",
                    currency="INR",
                    amount=10,
                )
            )


def test_database_failure_rolls_back_confirmation(monkeypatch):
    from profitlens import imports

    c = client()
    batch = preview(c, "invoices", [invoice(), invoice(id="I2")])
    original = imports.log_event

    def fail_second(conn, s, kind, record_id, action, snapshot):
        if record_id == "I2":
            raise RuntimeError("Simulated failure after insertion")
        return original(conn, s, kind, record_id, action, snapshot)

    monkeypatch.setattr(imports, "log_event", fail_second)
    with pytest.raises(RuntimeError):
        c.post(BASE + f"/imports/{batch['id']}/confirm")
    assert c.get(BASE + "/records/invoices").json() == []
    with db.engine.connect() as conn:
        assert (
            conn.execute(
                select(db.batches.c.state).where(db.batches.c.id == batch["id"])
            ).scalar_one()
            == "ready"
        )


def test_commit_failure_is_not_reported_as_success():
    from sqlalchemy import event

    signed = client()
    c = TestClient(
        app,
        headers={"Origin": settings.web_origin},
        cookies=signed.cookies,
        raise_server_exceptions=False,
    )

    def fail_commit(connection):
        raise RuntimeError("Simulated commit failure")

    event.listen(db.engine, "commit", fail_commit)
    try:
        response = c.post(BASE + "/records/invoices", json=invoice())
        assert response.status_code == 500
    finally:
        event.remove(db.engine, "commit", fail_commit)
    assert c.get(BASE + "/records/invoices").json() == []


def test_api_preserves_decimal_strings_and_analyst_record_scope():
    c = client()
    value = invoice(
        subtotal="999999999999.99", discount="0", tax="0", total="999999999999.99"
    )
    assert c.post(BASE + "/records/invoices", json=value).status_code == 201
    assert c.get(BASE + "/records/invoices/I1").json()["total"] == "999999999999.99"
    assert (
        c.post(
            BASE + "/records/invoices", json=invoice(id="PRIVATE", customer="C2")
        ).status_code
        == 201
    )
    a = client("analyst")
    assert [r["invoice_id"] for r in a.get(BASE + "/records/invoices").json()] == ["I1"]
    assert a.get(BASE + "/records/invoices/PRIVATE").status_code == 404


def test_presentation_seed_is_populated_separate_and_preserves_edits():
    from profitlens.demo import seed_presentation
    from profitlens.manage import seed_demo

    seed_demo(PASSWORD)
    with db.engine.begin() as conn:
        invoices = list(
            conn.execute(
                select(db.invoices).where(db.invoices.c.organization_id == "demo-org")
            ).mappings()
        )
        assert len({r["billing_period"] for r in invoices}) == 12
        assert sum(r["invoice_id"].startswith("READY-") for r in invoices) == 52
        assert not any(r["customer_id"].startswith("DEMO3-") for r in invoices)
        docs = list(
            conn.execute(
                select(db.contracts).where(db.contracts.c.organization_id == "demo-org")
            ).mappings()
        )
        assert {r["state"] for r in docs} == {"reviewed", "unreviewed"}
        assert all(
            (settings.storage_dir / "demo-org" / r["file_key"]).is_file() for r in docs
        )
        assert all(r["pages"][0]["text"] for r in docs)
        uid = conn.execute(
            select(db.users.c.id).where(db.users.c.email == "analyst@profitlens.local")
        ).scalar_one()
        conn.execute(delete(db.grants).where(db.grants.c.user_id == uid))
        conn.execute(
            db.invoices.update()
            .where(
                db.invoices.c.organization_id == "demo-org",
                db.invoices.c.invoice_id == "READY-I-01-2025-10",
            )
            .values(subtotal="12345", total="14145")
        )
        counts = {
            t.name: len(list(conn.execute(select(t))))
            for t in (db.customers, db.invoices, db.expenses, db.contracts)
        }
    seed_presentation()
    with db.engine.connect() as conn:
        assert counts == {
            t.name: len(list(conn.execute(select(t))))
            for t in (db.customers, db.invoices, db.expenses, db.contracts)
        }
        assert not conn.execute(
            select(db.grants).where(db.grants.c.user_id == uid)
        ).first()
        assert (
            conn.execute(
                select(db.invoices.c.subtotal).where(
                    db.invoices.c.organization_id == "demo-org",
                    db.invoices.c.invoice_id == "READY-I-01-2025-10",
                )
            ).scalar_one()
            == 12345
        )
    c = TestClient(app, headers={"Origin": settings.web_origin})
    assert (
        c.post(
            "/api/auth/login",
            json={"email": "karan@profitlens.local", "password": PASSWORD},
        ).status_code
        == 200
    )
    for doc in docs:
        response = c.get(f"/api/workspaces/demo-org/contracts/{doc['id']}/file")
        assert response.status_code == 200 and response.content.startswith(b"%PDF")
