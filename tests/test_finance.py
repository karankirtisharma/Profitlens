"""Golden financial examples independent of the database and UI."""

from datetime import date

import pytest
from fastapi import HTTPException
from profitlens.finance import calculate


def invoice(**changes):
    return (
        dict(
            organization_id="o",
            customer_id="c",
            billing_period="2026-09",
            currency="INR",
            invoice_id="I1",
            subtotal="1000.50",
            discount="100.25",
            tax="90.00",
            refund="50.25",
            total="940.00",
            source={"type": "csv", "filename": "golden.csv", "row": 2},
        )
        | changes
    )


def expense(**changes):
    return (
        dict(
            organization_id="o",
            customer_id="c",
            billing_period="2026-09",
            currency="INR",
            expense_id="E1",
            category="Delivery",
            amount="200.10",
        )
        | changes
    )


def contract(**changes):
    return (
        dict(
            organization_id="o",
            customer_id="c",
            id="DOC1",
            filename="contract.pdf",
            state="reviewed",
            currency="INR",
            effective_from=date(2026, 9, 1),
            effective_to=date(2026, 9, 30),
            source_page=1,
        )
        | changes
    )


def result(invoices=None, expenses=None, contracts=None):
    return calculate(
        "o",
        "c",
        "2026-09",
        "INR",
        invoices if invoices is not None else [invoice()],
        expenses if expenses is not None else [expense()],
        contracts if contracts is not None else [contract()],
    )


def codes(r):
    return {w["code"] for w in r["warnings"]}


def test_golden_revenue_costs_and_source_arithmetic():
    r = result(expenses=[expense(), expense(expense_id="E2", amount="0.20")])
    assert r["net_billed_revenue"] == "850.00"
    assert r["attributed_cost"] == "200.30"
    assert r["invoice_lines"][0]["tax_excluded"] == "90.00"
    assert r["invoice_lines"][0]["source"]["row"] == 2
    assert r["cost_completeness"] == "unverified"
    assert r["contracts"][0]["full_month_match"]
    assert codes(r) == {"cost_completeness_unverified"}


def test_missing_is_not_zero_and_explicit_zero_is_preserved():
    r = result(invoices=[], expenses=[])
    assert r["net_billed_revenue"] is None and r["attributed_cost"] is None
    assert {"missing_invoices", "missing_costs"} <= codes(r)
    r = result(
        invoices=[
            invoice(subtotal="100", discount="0", refund="100", tax="0", total="0")
        ],
        expenses=[expense(amount="0")],
    )
    assert r["net_billed_revenue"] == r["attributed_cost"] == "0.00"
    assert "zero_revenue" in codes(r) and "missing_costs" not in codes(r)
    assert "margin" not in r


def test_duplicate_ids_count_once_but_identical_amounts_different_ids_count_twice():
    r = result(invoices=[invoice(), invoice()])
    assert r["net_billed_revenue"] == "850.00" and "duplicate_record" in codes(r)
    r = result(invoices=[invoice(), invoice(invoice_id="I2")])
    assert r["net_billed_revenue"] == "1700.00" and "duplicate_record" not in codes(r)
    r = result(invoices=[invoice(), invoice(subtotal="1001.50", total="941.00")])
    assert r["net_billed_revenue"] is None and r["calculation_status"] == "blocked"


@pytest.mark.parametrize(
    "change,code",
    [
        ({"currency": "USD"}, "mixed_currency"),
        ({"customer_id": "other"}, "invalid_reference"),
        ({"organization_id": "other"}, "invalid_reference"),
        ({"billing_period": "2026-08"}, "invalid_reference"),
        ({"total": "939.99"}, "invalid_amount"),
        ({"refund": "1001"}, "invalid_amount"),
        ({"subtotal": "0.001"}, "invalid_amount"),
        ({"tax": "NaN"}, "invalid_amount"),
    ],
)
def test_invalid_inputs_block_only_affected_total(change, code):
    r = result(invoices=[invoice(**change)])
    assert r["net_billed_revenue"] is None and code in codes(r)
    assert r["attributed_cost"] == "200.10"


def test_invalid_and_duplicate_expenses_are_not_silently_summed():
    r = result(expenses=[expense(amount="-1")])
    assert r["attributed_cost"] is None and "invalid_amount" in codes(r)
    r = result(expenses=[expense(), expense()])
    assert r["attributed_cost"] == "200.10" and "duplicate_record" in codes(r)
    r = result(expenses=[expense(), expense(amount="201")])
    assert r["attributed_cost"] is None and "conflicting_duplicate" in codes(r)


@pytest.mark.parametrize(
    "contracts,expected",
    [
        ([], set()),
        (
            [contract(state="unreviewed")],
            {"unmatched_contract_period", "unreviewed_contract"},
        ),
        (
            [contract(effective_from=date(2026, 9, 2))],
            {"unmatched_contract_period", "partial_contract_period"},
        ),
        (
            [contract(effective_to=date(2026, 8, 31), effective_from=date(2026, 8, 1))],
            {"unmatched_contract_period"},
        ),
        ([contract(), contract(id="DOC2")], {"overlapping_contracts"}),
        (
            [contract(currency="USD")],
            {"contract_currency_mismatch", "unmatched_contract_period"},
        ),
    ],
)
def test_contract_coverage_does_not_invent_pricing_or_change_revenue(
    contracts, expected
):
    r = result(contracts=contracts)
    assert expected <= codes(r)
    assert r["net_billed_revenue"] == "850.00"
    if not contracts:
        assert r["contract_status"] == "not_provided"
        assert "unmatched_contract_period" not in codes(r)


def test_leap_month_and_invalid_period():
    r = calculate(
        "o",
        "c",
        "2024-02",
        "INR",
        [],
        [],
        [contract(effective_from=date(2024, 2, 1), effective_to=date(2024, 2, 29))],
    )
    assert r["contracts"][0]["full_month_match"]
    with pytest.raises(HTTPException):
        calculate("o", "c", "2026-13", "INR", [], [], [])


def test_large_decimal_sum_keeps_cents():
    rows = [
        invoice(
            invoice_id=f"I{i}",
            subtotal="999999999999.99",
            discount="0",
            refund="0",
            tax="0",
            total="999999999999.99",
        )
        for i in range(200)
    ]
    assert result(invoices=rows)["net_billed_revenue"] == "199999999999998.00"
