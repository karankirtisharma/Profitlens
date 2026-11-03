"""Accounting subledger tests use the same isolated _test fixture as workspace tests."""

from datetime import date
from decimal import Decimal

import pytest
from profitlens.operations import Payment, bucket
from pydantic import ValidationError


def test_bucket_keeps_unknown_due_dates_separate():
    rows = [
        {"total": Decimal("0.30"), "paid": Decimal("0.10"), "due_on": date(2026, 1, 1)},
        {"total": Decimal("20"), "paid": Decimal("0"), "due_on": None},
        {"total": Decimal("30"), "paid": Decimal("30"), "due_on": date(2026, 1, 1)},
    ]
    result = bucket(rows, date(2026, 2, 1))
    assert result["total"] == Decimal("20.20")
    assert result["overdue"] == Decimal("0.20")
    assert result["undated"] == Decimal("20")
    assert result["rows"][2]["status"] == "paid"


@pytest.mark.parametrize(
    "allocations",
    [
        [],
        [{"document_id": "A", "amount": "1.001"}],
        [{"document_id": "A", "amount": "0"}],
        [{"document_id": "A", "amount": "1"}, {"document_id": "A", "amount": "2"}],
    ],
)
def test_payment_schema_rejects_ambiguous_or_invalid_allocations(allocations):
    with pytest.raises(ValidationError):
        Payment(
            payment_id="P1",
            direction="received",
            paid_on="2026-01-01",
            currency="INR",
            allocations=allocations,
        )


def test_bill_opening_payment_requires_attestation_and_bound():
    from profitlens.operations import Bill

    payload = {
        "bill_id": "B",
        "vendor_id": "V",
        "issued_on": "2026-01-01",
        "currency": "INR",
        "total": "100",
        "opening_paid": "25",
        "payments_complete": True,
    }
    assert Bill(**payload).opening_paid == Decimal("25")
    with pytest.raises(ValidationError):
        Bill(**(payload | {"opening_paid": "101"}))
    with pytest.raises(ValidationError):
        Bill(**(payload | {"payments_complete": False}))
