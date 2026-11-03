"""Meaning-preserving bank/table imports; fixtures are synthetic, not bank exports."""

from decimal import Decimal

import pytest
from profitlens.source_api import bank_observation, parse_source_amount
from profitlens.source_parser import extract, suggestions


def test_tsv_keeps_unknown_columns_and_quoted_tabs():
    fmt, headers, rows, pages = extract(
        b'Date\tCredit\tDebit\tNote\n2026-11-01\t100.00\t\t"client\ttransfer"\n',
        "bank.tsv",
    )
    assert fmt == "tsv" and pages == []
    assert headers == ["Date", "Credit", "Debit", "Note"]
    assert rows[0]["Note"] == "client\ttransfer" and rows[0]["Debit"] == ""


@pytest.mark.parametrize(
    "filename", ["old.xls", "statement.ofx", "scan.png", "records.xml"]
)
def test_unsupported_formats_are_not_silently_parsed_as_csv(filename):
    with pytest.raises(ValueError, match="Supported sources"):
        extract(b"Amount,Date\n10,2026-11-01\n", filename)


def test_header_candidates_do_not_choose_ambiguous_money_fields():
    mapping = suggestions(["Money In", "Credit", "Money Out", "Qty", "UnitPrice"])
    assert mapping["credit"]["column"] == ""
    assert mapping["credit"]["confidence"] == "ambiguous"
    assert mapping["debit"]["column"] == "Money Out"
    assert mapping["quantity"]["column"] == "Qty"
    assert mapping["unit_price"]["column"] == "UnitPrice"


@pytest.mark.parametrize(
    "incoming,outgoing,convention,expected",
    [
        ("1,234.56", "", "dot", ("cash_inflow", Decimal("1234.56"))),
        ("0", "12,34", "comma", ("cash_outflow", Decimal("12.34"))),
        ("", "42", "dot", ("cash_outflow", Decimal("42"))),
    ],
)
def test_bank_direction_is_cash_not_profit(incoming, outgoing, convention, expected):
    assert bank_observation(incoming, outgoing, convention) == expected


@pytest.mark.parametrize(
    "incoming,outgoing",
    [
        ("", ""),
        ("0", "0"),
        ("10", "5"),
        ("-5", ""),
        ("5", "-1"),
        ("NaN", ""),
        ("Infinity", ""),
        ("1.001", ""),
        ("1,23", ""),
    ],
)
def test_ambiguous_or_invalid_bank_rows_require_review(incoming, outgoing):
    with pytest.raises(ValueError):
        bank_observation(incoming, outgoing, "dot")


def test_missing_direct_money_is_not_zero():
    with pytest.raises(ValueError):
        parse_source_amount("", "dot")
    assert parse_source_amount("0", "dot") == Decimal("0")
    assert parse_source_amount("(1.234,56)", "comma") == Decimal("-1234.56")
