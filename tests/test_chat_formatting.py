"""Formatting must not invent date precision or change supplied evidence."""

from profitlens.chat import canonical_reply


def pack():
    return {
        "metrics": {},
        "facts": {
            "selected_period": "2026-09",
            "document_aa_start": "2026-09-01",
            "document_aa_end": "2026-09-30",
        },
    }


def test_month_summary_does_not_expand_into_contract_day():
    assert (
        canonical_reply("Margin for September 2026", pack())
        == "Margin for {{selected_period}}"
    )
    assert (
        canonical_reply("Margin for Sep 2026", pack())
        == "Margin for {{selected_period}}"
    )


def test_explicit_document_date_retains_its_day():
    assert (
        canonical_reply("Ends on 30 September 2026", pack())
        == "Ends on {{document_aa_end}}"
    )
    assert (
        canonical_reply("Starts on 2026-09-01", pack())
        == "Starts on {{document_aa_start}}"
    )


def test_unknown_day_is_not_silently_accepted_as_known_month():
    text = canonical_reply("Ends on 29 September 2026", pack())
    assert "29" in text  # Remaining digits are rejected by the response verifier.
    assert "document_aa_end" not in text
