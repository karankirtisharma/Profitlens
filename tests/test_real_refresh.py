"""Optional local verification of downloaded public data; never downloads in CI."""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from test_workspace import TEST_URL, client
from test_workspace import fixture_data as fixture_data
from test_workspace import hash_password as hash_password
from test_workspace import migrated_database as migrated_database

ROOT = Path("data/private/dwp-2026")
pytestmark = pytest.mark.skipif(
    not TEST_URL or not (ROOT / "demo-subset.csv").exists(),
    reason="Requires local downloaded licensed data and test database",
)


def test_real_source_preview_confirm_totals_trace_and_duplicates():
    # Test workspace uses INR; set its declared currency to GBP before importing.
    from profitlens import database as db

    with db.engine.begin() as conn:
        conn.execute(
            db.organizations.update()
            .where(db.organizations.c.id == "a")
            .values(currency="GBP")
        )
    c = client()
    base = "/api/workspaces/a"
    path = ROOT / "demo-subset.csv"
    doc = c.post(
        base + "/sources",
        data={"adapter": "generic"},
        files={"file": (path.name, path.read_bytes(), "text/csv")},
    )
    assert doc.status_code in (200, 201), doc.text
    key = doc.json()["id"]
    mapping = {
        "kind": "expenditure",
        "currency": "GBP",
        "columns": {
            "amount": "Amount",
            "date": "Date",
            "description": "Invoice Account Description",
            "counterparty": "Supplier Name",
        },
    }
    preview = c.post(base + f"/sources/{key}/preview", json=mapping)
    assert preview.status_code == 200, preview.text
    assert preview.json()["issues"] == []
    for _ in range(2):
        result = c.post(
            base + f"/sources/{key}/confirm",
            json={"preview_token": preview.json()["preview_token"]},
        )
        assert result.status_code == 200, result.text
    facts = c.get(base + "/facts").json()
    truth = json.loads((ROOT / "ground-truth.json").read_text())
    assert facts["total"] == 600
    assert Decimal(facts["groups"][0]["amount"]) == Decimal(truth["amount"])
    dashboard = c.get(base + "/dashboard").json()
    actual = {r["period"]: Decimal(r["amount"]) for r in dashboard["source_series"]}
    assert actual == {k: Decimal(v) for k, v in truth["per_month"].items()}
    assert dashboard["verified_net_revenue"] is None
    detail = c.get(base + f"/facts/{facts['rows'][0]['id']}").json()
    assert detail["raw"]["Original URL"].startswith(
        "https://assets.publishing.service.gov.uk/"
    )
    assert c.get(base + f"/sources/{key}/file").content == path.read_bytes()
    assert client("outsider").get(base + f"/sources/{key}/file").status_code == 404
