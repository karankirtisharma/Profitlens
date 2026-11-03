"""Verify the published synthetic workflow through the same authenticated APIs."""

import importlib.util
from pathlib import Path

import pytest
from test_workspace import TEST_URL, client
from test_workspace import fixture_data as fixture_data
from test_workspace import hash_password as hash_password
from test_workspace import migrated_database as migrated_database

pytestmark = pytest.mark.skipif(
    not TEST_URL, reason="Requires dedicated PostgreSQL test database"
)


def test_complete_synthetic_showcase_and_retry():
    spec = importlib.util.spec_from_file_location(
        "showcase", Path("scripts/datasets/showcase_2026.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    c = client()
    result = module.populate(c, "/api/workspaces/a")
    assert result["dashboard"]["counts"]["invoices"] == 37
    assert result["dashboard"]["counts"]["expenses"] == 72
    assert result["dashboard"]["counts"]["reviewed_contracts"] == 4
    assert result["balances"]["payables"]["total"] == "5000.00"
    second = module.populate(c, "/api/workspaces/a")
    assert second["dashboard"]["counts"] == result["dashboard"]["counts"]
    assert second["balances"] == result["balances"]
