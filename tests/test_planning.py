"""Deterministic recurrence and real database financial boundary tests."""

from datetime import date

import pytest
from profitlens.planning import next_date
from test_workspace import TEST_URL, client
from test_workspace import fixture_data as fixture_data
from test_workspace import hash_password as hash_password
from test_workspace import migrated_database as migrated_database

pytestmark = pytest.mark.skipif(not TEST_URL, reason="Requires isolated test database")
BASE = "/api/workspaces/a/planning"


def schedule(c, **kw):
    return c.post(
        BASE + "/recurring",
        json={
            "id": "RET",
            "name": "Support retainer",
            "customer_id": "C1",
            "start_on": "2026-01-31",
            "end_on": "2026-03-31",
            "currency": "INR",
            "subtotal": "100",
            "discount": "10",
            "tax": "9",
            **kw,
        },
    )


def test_calendar_anchor_and_draft_issue_retry():
    assert next_date(date(2024, 1, 31), date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert next_date(date(2024, 1, 31), date(2024, 2, 29), 1) == date(2024, 3, 31)
    c = client()
    assert schedule(c).status_code == 200
    assert c.post(BASE + "/recurring/generate").json()["generated"] == 3
    assert c.post(BASE + "/recurring/generate").json()["generated"] == 0
    drafts = c.get(BASE + "/recurring").json()["drafts"]
    assert sorted(d["issued_on"] for d in drafts) == [
        "2026-01-31",
        "2026-02-28",
        "2026-03-31",
    ]
    assert (
        c.get("/api/workspaces/a/operations/summary").json()["receivables"]["rows"]
        == []
    )
    key = drafts[0]["id"]
    issued = c.post(BASE + f"/drafts/{key}/issue")
    assert issued.status_code == 200, issued.text
    assert c.post(BASE + f"/drafts/{key}/issue").json()["already_issued"] is True
    assert (
        c.get("/api/workspaces/a/operations/summary").json()["receivables"]["total"]
        == "99.00"
    )
    assert c.post(BASE + f"/drafts/{key}/skip").status_code == 409
    assert c.post(BASE + f"/drafts/{drafts[1]['id']}/skip").status_code == 200


def test_paused_future_invalid_and_authorization():
    c = client()
    assert schedule(c, end_on=None).status_code == 200
    assert (
        c.put(BASE + "/recurring/RET/state", json={"state": "paused"}).status_code
        == 200
    )
    assert c.post(BASE + "/recurring/generate").json()["generated"] == 0
    assert schedule(c).status_code == 409
    assert schedule(c, id="BAD", discount="110").status_code == 422
    assert schedule(c, id="FOREIGN", customer_id="B1").status_code == 404
    assert schedule(c, id="FX", currency="USD").status_code == 422
    assert client("analyst").get(BASE + "/recurring").status_code == 403
    assert client("outsider").post(BASE + "/recurring/generate").status_code == 404
    assert (
        c.put(BASE + "/recurring/RET/state", json={"state": "active"}).status_code
        == 200
    )
    assert c.post(BASE + "/recurring/generate").json()["generated"] > 0


def order(c, **kw):
    return c.post(
        BASE + "/orders",
        json={
            "id": "PO1",
            "vendor_id": "V1",
            "ordered_on": "2026-01-01",
            "currency": "INR",
            "lines": [
                {
                    "description": "Support",
                    "quantity": "2.5",
                    "unit_price": "10.01",
                    "tax": "1",
                }
            ],
            **kw,
        },
    )


def test_order_commitment_conversion_and_payments():
    c = client()
    assert (
        c.post(
            "/api/workspaces/a/operations/vendors",
            json={"vendor_id": "V1", "name": "Supplier"},
        ).status_code
        == 200
    )
    r = order(c)
    assert r.status_code == 200, r.text
    assert r.json()["total"] == "26.03"
    assert (
        c.get("/api/workspaces/a/operations/summary").json()["payables"]["total"] == "0"
    )
    payload = {
        "bill_id": "B1",
        "issued_on": "2026-01-10",
        "opening_paid": "0",
        "payments_complete": True,
        "invoice_matches_order": True,
    }
    assert c.put(BASE + "/orders/PO1/bill", json=payload).status_code == 409
    assert c.post(BASE + "/orders/PO1/approve").status_code == 200
    assert c.put(BASE + "/orders/PO1/bill", json=payload).status_code == 200
    assert (
        c.put(BASE + "/orders/PO1/bill", json=payload).json()["already_converted"]
        is True
    )
    assert (
        c.get("/api/workspaces/a/operations/summary").json()["payables"]["total"]
        == "26.03"
    )
    assert c.post(BASE + "/orders/PO1/cancel").status_code == 409
    assert (
        c.post(
            "/api/workspaces/a/operations/payments",
            json={
                "payment_id": "P1",
                "direction": "made",
                "paid_on": "2026-02-01",
                "currency": "INR",
                "allocations": [{"document_id": "B1", "amount": "6.03"}],
            },
        ).status_code
        == 200
    )
    assert (
        c.get("/api/workspaces/a/operations/summary").json()["payables"]["total"]
        == "20.00"
    )
    assert order(c).status_code == 409
    assert client("outsider").get(BASE + "/orders").status_code == 404
    assert client("analyst").post(BASE + "/orders/PO1/approve").status_code == 403


def test_order_invalid_links_cancel_and_attestation():
    c = client()
    assert order(c).status_code == 404
    c.post(
        "/api/workspaces/a/operations/vendors",
        json={"vendor_id": "V1", "name": "Supplier"},
    )
    assert (
        order(
            c,
            lines=[
                {
                    "item_id": "UNKNOWN",
                    "description": "bad",
                    "quantity": 1,
                    "unit_price": 1,
                }
            ],
        ).status_code
        == 422
    )
    assert order(c).status_code == 200
    assert c.post(BASE + "/orders/PO1/cancel").status_code == 200
    assert c.post(BASE + "/orders/PO1/approve").status_code == 409
    assert (
        c.put(
            BASE + "/orders/PO1/bill",
            json={"bill_id": "B1", "issued_on": "2026-01-01", "opening_paid": "0"},
        ).status_code
        == 422
    )
