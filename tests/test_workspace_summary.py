"""Workspace aggregation uses exact arithmetic and existing database visibility."""

import pytest
from profitlens import database as db
from profitlens import workspace_summary
from profitlens.security import scope
from sqlalchemy import delete
from test_analysis import setup
from test_workspace import TEST_URL, client
from test_workspace import fixture_data as fixture_data
from test_workspace import hash_password as hash_password
from test_workspace import migrated_database as migrated_database

pytestmark = pytest.mark.skipif(not TEST_URL, reason="Dedicated test database required")


def summary(user="admin", period="2026-09"):
    with db.engine.begin() as conn:
        return workspace_summary.summarize(conn, scope("a", {"id": user}, conn), period)


def test_aggregate_and_analyst_visibility():
    c = client()
    setup(c)
    setup(c, customer="C2", cost="80", suffix="2")
    result = summary()
    assert result["metrics"]["net_billed_revenue"]["value"] == "180.00"
    assert result["metrics"]["contribution"]["value"] == "60.00"
    assert result["metrics"]["margin_percent"]["value"] == "33.33"
    assert result["status"] == "provisional"
    limited = summary("analyst")
    assert limited["metrics"]["contribution"]["value"] == "50.00"
    assert [r["customer_id"] for r in limited["items"]] == ["C1"]


def test_missing_cost_is_not_zero_and_empty_month_is_not_latest():
    c = client()
    setup(c)
    setup(c, customer="C2", suffix="2")
    with db.engine.begin() as conn:
        conn.execute(delete(db.expenses).where(db.expenses.c.expense_id == "E2"))
    result = summary()
    assert result["status"] == "unavailable"
    assert "contribution" not in result["metrics"]
    assert "attributed_cost" not in result["metrics"]
    assert result["metrics"]["missing_cost_customers"]["value"] == "1"
    empty = summary(period="2026-10")
    assert empty["status"] == "no_records"
    assert "net_billed_revenue" not in empty["metrics"]


def test_authorized_navigation_and_status_cards():
    pack = dict(
        customer_id="C1",
        billing_period="2026-09",
        metrics={"contribution": {"value": "-10", "unit": "INR"}},
        profitability_status="provisional",
        invoice_lines=[{"id": "I"}],
        expense_lines=[],
        documents=[],
    )
    result = workspace_summary.presentation(pack, "analyst")
    assert not any(a["view"] == "imports" for a in result["actions"])
    assert any(a["record_id"] == "I" for a in result["actions"])
    assert result["cards"][2]["tone"] == "negative"
    assert result["cards"][1]["value"] == "Unavailable"


def test_rejected_financial_rows_cannot_disappear_from_aggregate():
    c = client()
    setup(c)
    with db.engine.begin() as conn:
        conn.execute(db.invoices.update().values(currency="USD"))
        conn.execute(db.expenses.update().values(currency="USD"))
    result = summary()
    assert len(result["items"]) == 1
    assert result["status"] == "unavailable"
    assert "contribution" not in result["metrics"]
