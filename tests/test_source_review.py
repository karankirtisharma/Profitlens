"""Monthly source reviews disclose missing coverage and preserve exact arithmetic."""

from datetime import date
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException
from profitlens.source_review import assemble_review, month_bounds


def review(rows, **kwargs):
    return assemble_review(
        rows,
        period=kwargs.pop("period", "2026-02"),
        kind="expenditure",
        currency="GBP",
        organization_id="a",
        today=date(2026, 11, 3),
        **kwargs,
    )


def group(side, name, amount, count=1):
    return {
        "side": side,
        "counterparty": name,
        "amount": Decimal(amount),
        "count": count,
    }


def test_decimal_credit_and_zero_have_distinct_meanings_from_missing():
    result = review(
        [
            group("current", "Supplier", "0.10"),
            group("current", "Credit", "-0.10"),
            group("previous", "Supplier", "0.30"),
        ]
    )
    assert result["current"]["amount"] == "0.00"
    assert result["current"]["count"] == 2
    assert result["change"] == "-0.30"
    assert result["drivers"][0]["change"] == "-0.20"
    assert result["drivers"][1]["previous"] is None
    assert result["drivers"][1]["change"] is None
    assert result["drivers"][1]["status"] == "current_only"
    empty = review([])
    assert empty["current"]["amount"] is None
    assert empty["change"] is None
    assert empty["comparable"] is False


def test_missing_month_is_not_zero_or_disappearance():
    result = review([group("previous", "A", "500")])
    assert result["current"]["amount"] is None
    assert result["previous"]["amount"] == "500"
    assert result["comparable"] is False
    assert result["change"] is None
    assert result["drivers"][0]["status"] == "previous_only"
    assert result["drivers"][0]["change"] is None


def test_exact_labels_unknown_labels_and_safe_evidence_urls():
    result = review(
        [
            group("previous", "ACME", "10"),
            group("current", "Acme", "20"),
            group("current", "A&B /?", "30"),
            group("current", "", "40", 2),
        ],
        missing_dates=3,
    )
    assert result["driver_group_count"] == 4
    assert all(r["change"] is None for r in result["drivers"])
    assert result["unknown_counterparty_records"] == 2
    assert result["missing_dates"] == 3
    unknown = next(r for r in result["drivers"] if r["counterparty"] == "")
    assert unknown["label"] == "Unknown counterparty"
    assert "counterparty=" in unknown["current_source_url"]
    named = next(r for r in result["drivers"] if r["counterparty"] == "A&B /?")
    params = parse_qs(urlparse(named["current_source_url"]).query)
    assert params == {
        "currency": ["GBP"],
        "kind": ["expenditure"],
        "start": ["2026-02-01"],
        "end": ["2026-02-28"],
        "counterparty": ["A&B /?"],
    }


def test_top_changes_are_ranked_by_absolute_value_and_bounded():
    rows = [
        g
        for i in range(9)
        for g in (
            group("previous", str(i), "100"),
            group("current", str(i), str(100 - i)),
        )
    ]
    rows += [group("current", "new" + str(i), str(i)) for i in range(9)]
    result = review(rows)
    assert len(result["drivers"]) == 8
    assert [r["change"] for r in result["drivers"][:5]] == [
        "-8",
        "-7",
        "-6",
        "-5",
        "-4",
    ]
    assert result["driver_group_count"] == 18
    assert "may not explain the full total" in result["notice"]


def test_calendar_boundaries_and_incomplete_current_month():
    assert month_bounds("2024-03") == (
        date(2024, 2, 1),
        date(2024, 3, 1),
        date(2024, 4, 1),
    )
    assert month_bounds("2026-01")[0] == date(2025, 12, 1)
    assert review([], period="2026-11")["current_month_incomplete"] is True
    assert review([], period="2026-10")["current_month_incomplete"] is False
    for invalid in ("2026-13", "0000-01", "0001-01", "9999-12"):
        with pytest.raises(HTTPException) as exc:
            month_bounds(invalid)
        assert exc.value.status_code == 422
