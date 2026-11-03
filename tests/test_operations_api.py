"""HTTP + PostgreSQL coverage for payment allocations and supplier accounts."""

import pytest
from profitlens import database as db
from sqlalchemy import select
from test_workspace import (
    TEST_URL,
    client,
)  # noqa: F401
from test_workspace import fixture_data as fixture_data
from test_workspace import hash_password as hash_password
from test_workspace import migrated_database as migrated_database

pytestmark = pytest.mark.skipif(
    not TEST_URL, reason="Requires isolated _test PostgreSQL database"
)
BASE = "/api/workspaces/a/operations"


def invoice(c, key="I1", customer="C1", total="100.00"):
    response = c.post(
        "/api/workspaces/a/records/invoices",
        json={
            "invoice_id": key,
            "customer_id": customer,
            "billing_period": "2026-01",
            "currency": "INR",
            "subtotal": total,
            "tax": "0",
            "discount": "0",
            "refund": "0",
            "total": total,
        },
    )
    assert response.status_code == 201, response.text


def enroll(c, key="I1", paid="0"):
    response = c.put(
        BASE + f"/invoice-terms/{key}",
        json={"due_on": "2026-02-01", "opening_paid": paid, "payments_complete": True},
    )
    assert response.status_code == 200, response.text


def pay(c, allocations, key="P1", direction="received", **kw):
    return c.post(
        BASE + "/payments",
        json={
            "payment_id": key,
            "direction": direction,
            "paid_on": "2026-03-01",
            "currency": "INR",
            "allocations": [{"document_id": k, "amount": v} for k, v in allocations],
            **kw,
        },
    )


def test_partial_payment_multiple_invoices_exact_balances_and_retry():
    c = client()
    invoice(c)
    invoice(c, "I2", total="200")
    before = c.get(BASE + "/summary").json()
    assert before["receivables"]["untracked_count"] == 2
    assert before["receivables"]["rows"] == []
    enroll(c, paid="10")
    enroll(c, "I2")
    response = pay(c, [("I1", "40.10"), ("I2", "100.20")])
    assert response.status_code == 200, response.text
    assert response.json()["total"] == "140.30"
    assert pay(c, [("I1", "1")]).status_code == 409
    summary = c.get(BASE + "/summary").json()["receivables"]
    assert summary["total"] == "149.70"
    assert summary["overdue"] == "149.70"
    assert pay(c, [("I1", "49.91")], key="P2").status_code == 422
    assert len(c.get(BASE + "/payments").json()) == 1
    assert len(c.get(BASE + "/payments").json()[0]["allocations"]) == 2
    with db.engine.connect() as conn:
        assert (
            conn.scalar(
                select(db.invoices.c.total).where(db.invoices.c.invoice_id == "I1")
            )
            == 100
        )
        assert conn.execute(
            select(db.audit).where(db.audit.c.kind == "payments")
        ).first()


def test_party_currency_scope_and_unenrolled_protection():
    c = client()
    invoice(c)
    assert pay(c, [("I1", "1")]).status_code == 422
    enroll(c)
    invoice(c, "I2", customer="C2")
    enroll(c, "I2")
    assert pay(c, [("I1", "1"), ("I2", "1")]).status_code == 422
    assert pay(c, [("I1", "1")], currency="USD").status_code == 422
    assert pay(c, [("MISSING", "1")]).status_code == 404
    assert client("analyst").get(BASE + "/summary").status_code == 403
    assert client("outsider").get(BASE + "/payments").status_code == 404
    assert (
        c.put(
            BASE + "/invoice-terms/I1",
            json={"opening_paid": "0", "payments_complete": True},
        ).status_code
        == 409
    )
    assert c.get(BASE + "/payments").json() == []


def test_vendor_bills_partial_payment_and_due_rules():
    c = client()
    assert (
        c.post(
            BASE + "/vendors", json={"vendor_id": "V1", "name": "A supplier"}
        ).status_code
        == 200
    )
    bill = {
        "bill_id": "B1",
        "vendor_id": "V1",
        "issued_on": "2026-01-01",
        "due_on": None,
        "currency": "INR",
        "total": "75.15",
        "opening_paid": "0",
        "payments_complete": True,
    }
    assert c.post(BASE + "/bills", json=bill).status_code == 200
    assert c.post(BASE + "/bills", json=bill).status_code == 409
    assert (
        c.post(
            BASE + "/bills", json=bill | {"bill_id": "B2", "vendor_id": "OTHER"}
        ).status_code
        == 404
    )
    assert (
        c.post(
            BASE + "/bills", json=bill | {"bill_id": "B2", "due_on": "2025-12-31"}
        ).status_code
        == 422
    )
    assert pay(c, [("B1", "25.10")], direction="made").status_code == 200
    summary = c.get(BASE + "/summary").json()
    assert summary["payables"]["undated"] == "50.05"
    assert summary["payables"]["overdue"] == "0"
    assert pay(c, [("B1", "50.06")], key="P2", direction="made").status_code == 422
    assert (
        pay(
            c, [("B1", "1")], key="P2", direction="made", paid_on="2025-12-01"
        ).status_code
        == 422
    )
    assert pay(c, [("B1", "50.05")], key="P2", direction="made").status_code == 200
    assert c.get(BASE + "/summary").json()["payables"]["rows"][0]["status"] == "paid"
    with db.engine.connect() as conn:
        assert conn.execute(select(db.expenses)).first() is None


def test_items_and_enrollment_validation():
    c = client()
    item = {
        "item_id": "S1",
        "name": "Consulting hour",
        "unit_price": "10.25",
        "currency": "INR",
    }
    assert c.post(BASE + "/items", json=item).status_code == 200
    assert (
        c.put(BASE + "/items/S1", json=item | {"unit_price": "11.25"}).status_code
        == 200
    )
    assert c.get(BASE + "/items").json()[0]["unit_price"] == "11.25"
    assert (
        c.post(
            BASE + "/items", json=item | {"item_id": "S2", "currency": "USD"}
        ).status_code
        == 422
    )
    invoice(c)
    assert (
        c.put(
            BASE + "/invoice-terms/I1",
            json={"opening_paid": "101", "payments_complete": True},
        ).status_code
        == 422
    )
    assert (
        c.put(
            BASE + "/invoice-terms/I1",
            json={"opening_paid": "0", "payments_complete": False},
        ).status_code
        == 422
    )
    enroll(c)
    # Changing a tracked invoice would invalidate allocations and must be blocked.
    update = {
        "invoice_id": "I1",
        "customer_id": "C1",
        "billing_period": "2026-01",
        "currency": "INR",
        "subtotal": "90",
        "discount": "0",
        "tax": "0",
        "refund": "0",
        "total": "90",
    }
    assert (
        c.put("/api/workspaces/a/records/invoices/I1", json=update).status_code == 409
    )


def test_failed_allocation_rolls_back_whole_payment_and_source_sales_are_not_receivables():
    c = client()
    invoice(c)
    invoice(c, "I2")
    enroll(c)
    enroll(c, "I2")
    assert pay(c, [("I1", "20"), ("I2", "101")]).status_code == 422
    assert c.get(BASE + "/payments").json() == []
    assert c.get(BASE + "/summary").json()["receivables"]["total"] == "200.00"
    with db.engine.begin() as conn:
        conn.execute(
            db.invoices.insert().values(
                organization_id="a",
                invoice_id="SALES",
                customer_id="C1",
                billing_period="2026-01",
                currency="INR",
                amount_basis="reported_sales",
                subtotal=None,
                discount=None,
                tax=None,
                refund=None,
                total="50",
            )
        )
    assert (
        c.put(
            BASE + "/invoice-terms/SALES",
            json={"opening_paid": "0", "payments_complete": True},
        ).status_code
        == 422
    )
    assert "SALES" not in [
        r["invoice_id"] for r in c.get(BASE + "/invoice-candidates").json()
    ]
    assert c.get(BASE + "/summary").json()["receivables"]["untracked_count"] == 1


def test_supplier_and_catalog_information_never_leaks_to_customer_scoped_analysts():
    c = client("analyst")
    for endpoint in (
        "vendors",
        "items",
        "bills",
        "payments",
        "invoice-candidates",
        "summary",
    ):
        assert c.get(BASE + "/" + endpoint).status_code == 403
    assert (
        client("outsider")
        .post(BASE + "/vendors", json={"vendor_id": "V", "name": "Wrong scope"})
        .status_code
        == 404
    )


def test_void_payment_restores_balance_preserves_evidence_and_allows_correction():
    c = client()
    invoice(c)
    enroll(c)
    assert pay(c, [("I1", "60")]).status_code == 200
    assert c.get(BASE + "/summary").json()["receivables"]["total"] == "40.00"
    assert c.post(BASE + "/payments/P1/void", json={"reason": " "}).status_code == 422
    assert (
        client("outsider")
        .post(BASE + "/payments/P1/void", json={"reason": "No access"})
        .status_code
        == 404
    )
    response = c.post(
        BASE + "/payments/P1/void",
        json={"reason": "Wrong bank reference; corrected separately"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "void"
    assert c.get(BASE + "/summary").json()["receivables"]["total"] == "100.00"
    row = c.get(BASE + "/payments").json()[0]
    assert row["state"] == "void"
    assert row["allocations"][0]["amount"] == "60.00"
    assert (
        c.post(BASE + "/payments/P1/void", json={"reason": "Again"}).status_code == 409
    )
    assert pay(c, [("I1", "100")], key="CORRECTED").status_code == 200
    assert c.get(BASE + "/summary").json()["receivables"]["total"] == "0.00"
    with db.engine.connect() as conn:
        row = conn.execute(
            select(db.audit.c.snapshot).where(
                db.audit.c.kind == "payments", db.audit.c.action == "voided"
            )
        ).scalar_one()
        assert row["before"]["state"] == "active"
        assert row["after"]["state"] == "void"


def test_bill_opening_paid_and_void_disbursement():
    c = client()
    assert (
        c.post(BASE + "/vendors", json={"vendor_id": "V", "name": "Vendor"}).status_code
        == 200
    )
    bill = {
        "bill_id": "B",
        "vendor_id": "V",
        "issued_on": "2026-01-01",
        "currency": "INR",
        "total": "100",
        "opening_paid": "25",
        "payments_complete": True,
    }
    assert c.post(BASE + "/bills", json=bill).status_code == 200
    assert c.get(BASE + "/summary").json()["payables"]["total"] == "75.00"
    assert pay(c, [("B", "75.01")], direction="made").status_code == 422
    assert pay(c, [("B", "75")], direction="made").status_code == 200
    assert c.get(BASE + "/summary").json()["payables"]["total"] == "0.00"
    assert (
        c.post(
            BASE + "/payments/P1/void", json={"reason": "Duplicate entry"}
        ).status_code
        == 200
    )
    assert c.get(BASE + "/summary").json()["payables"]["total"] == "75.00"
