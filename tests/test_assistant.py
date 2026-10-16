"""Automatic chat planning and permission boundaries, with a mocked hosted model."""

import pytest
from profitlens import assistant, chat, explanations
from profitlens import database as db
from sqlalchemy import delete
from test_analysis import setup
from test_workspace import BASE, TEST_URL, client
from test_workspace import fixture_data as fixture_data
from test_workspace import hash_password as hash_password
from test_workspace import migrated_database as migrated_database

pytestmark = pytest.mark.skipif(not TEST_URL, reason="Dedicated test database required")


def mock_model(monkeypatch, customer=None, period="2026-09", record=None, hook=None):
    captured = []
    monkeypatch.setattr(explanations, "provider_status", lambda: {"configured": True})

    def complete(schema, prompt, payload, **kw):
        captured.append(payload)
        if schema is assistant.Plan:
            if hook:
                hook()
            return assistant.Plan(
                intent="invoices" if record else "overview",
                customer_id=customer,
                billing_period=period,
                record_id=record,
                clarification="",
                resolution="resolved",
            )
        evidence = payload["CURRENT_EVIDENCE"]
        assert "invoice_lines" not in evidence
        return chat.ChatAnswer(
            reply="**Contribution** is {{contribution}}."
            if "contribution" in evidence["metrics"]
            else "**Evidence missing:** no complete financial calculation is available.",
            insufficient_evidence="contribution" not in evidence["metrics"],
            finding_ids=[],
            source_ids=[],
        )

    monkeypatch.setattr(explanations, "structured_completion", complete)
    return captured


def ask(c, **kw):
    return c.post(
        BASE + "/chat",
        json={"message": "How is profit in September 2026?", "automatic": True, **kw},
    )


def test_greeting_skips_financial_retrieval(monkeypatch):
    c = client()
    setup(c)
    monkeypatch.setattr(explanations, "provider_status", lambda: {"configured": True})

    def complete(schema, prompt, payload, **kw):
        if schema is assistant.Plan:
            return assistant.Plan(
                intent="conversation",
                customer_id="C1",
                billing_period="2026-09",
                record_id=None,
                clarification="",
                resolution="resolved",
            )
        evidence = payload["CURRENT_EVIDENCE"]
        assert evidence["scope_mode"] == "conversation"
        assert not evidence["metrics"] and not evidence["documents"]
        assert evidence["billing_period"] is None
        return chat.ChatAnswer(
            reply="Hi! I'm ProfitLens. How can I help?",
            conversational=True,
            insufficient_evidence=False,
            finding_ids=[],
            source_ids=[],
        )

    def forbidden(*args, **kwargs):
        pytest.fail("Greeting must not calculate financial summaries")

    monkeypatch.setattr(explanations, "structured_completion", complete)
    monkeypatch.setattr(assistant.workspace_summary, "summarize", forbidden)
    r = ask(c, message="hi")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["reply"].startswith("Hi!")
    assert data["billing_period"] is None
    assert not any(
        data[k]
        for k in (
            "cards",
            "actions",
            "metrics",
            "sources",
            "notice",
            "insufficient_evidence",
        )
    )


def test_automatic_workspace_total_and_navigation(monkeypatch):
    c = client()
    setup(c)
    setup(c, customer="C2", suffix="2", cost="80")
    calls = mock_model(monkeypatch)
    r = ask(c)
    assert r.status_code == 200, r.text
    assert "60.00 INR" in r.json()["reply"]
    assert r.json()["scope_label"] == "All accessible customers"
    assert len(calls) == 2
    assert any(a["record_id"] == "I" for a in r.json()["actions"])


def test_analyst_catalog_and_totals_exclude_ungranted_customers(monkeypatch):
    c = client()
    setup(c)
    setup(c, customer="C2", suffix="2")
    calls = mock_model(monkeypatch)
    r = ask(client("analyst"))
    assert r.status_code == 200, r.text
    assert [v["customer_id"] for v in calls[0]["catalog"]["customers"]] == ["C1"]
    assert "50.00 INR" in r.json()["reply"]
    assert not any(a["view"] == "imports" for a in r.json()["actions"])


def test_planner_cannot_select_unauthorized_customer(monkeypatch):
    calls = mock_model(monkeypatch, customer="C2")
    r = ask(client("analyst"))
    assert r.status_code == 404
    assert len(calls) == 1


def test_record_lookup_respects_access_and_resolves_stored_period(monkeypatch):
    c = client()
    setup(c)
    setup(c, customer="C2", suffix="2")
    mock_model(monkeypatch, record="I2")
    assert ask(client("analyst")).status_code == 404
    mock_model(monkeypatch, record="I", period="2026-10")
    r = ask(c)
    assert r.status_code == 200, r.text
    assert r.json()["billing_period"] == "2026-09"
    assert r.json()["actions"][0]["record_id"] == "I"


def test_month_with_no_data_is_not_replaced_by_latest(monkeypatch):
    c = client()
    setup(c)
    calls = mock_model(monkeypatch, period="2026-10")
    r = ask(c)
    assert r.status_code == 200, r.text
    assert r.json()["billing_period"] == "2026-10"
    assert r.json()["profitability_status"] == "no_records"
    assert calls[1]["CURRENT_EVIDENCE"]["facts"]["latest_record_period"] == "2026-09"
    assert r.json()["cards"][2]["value"] == "Unavailable"


def test_permission_revocation_during_planning_discards_response(monkeypatch):
    def revoke():
        with db.engine.begin() as conn:
            conn.execute(delete(db.grants).where(db.grants.c.user_id == "analyst"))

    calls = mock_model(monkeypatch, hook=revoke)
    assert ask(client("analyst")).status_code == 409
    assert len(calls) == 1


def test_bad_planned_period_is_rejected_before_data_query(monkeypatch):
    calls = mock_model(monkeypatch, period="2026-99")
    assert ask(client()).status_code == 422
    assert len(calls) == 1


def test_this_month_is_calendar_month_even_if_planner_suggests_latest(monkeypatch):
    calls = mock_model(monkeypatch, period="2026-09")
    r = ask(client(), message="How is profit this month?")
    assert r.status_code == 200, r.text
    assert r.json()["billing_period"] == calls[0]["catalog"]["today"][:7]


def test_clarification_never_returns_guessed_financial_cards(monkeypatch):
    c = client()
    setup(c)
    monkeypatch.setattr(explanations, "provider_status", lambda: {"configured": True})

    def model(schema, prompt, payload, **kw):
        if schema is assistant.Plan:
            return assistant.Plan(
                intent="overview",
                customer_id=None,
                billing_period="2026-09",
                record_id=None,
                clarification="Which month should I inspect?",
                resolution="unsupported_range",
            )
        assert payload["CURRENT_EVIDENCE"]["metrics"] == {}
        return chat.ChatAnswer(
            reply="Which month should I inspect?",
            insufficient_evidence=True,
            finding_ids=[],
            source_ids=[],
        )

    monkeypatch.setattr(explanations, "structured_completion", model)
    r = ask(c, message="Compare the whole year")
    assert r.status_code == 200, r.text
    assert not r.json()["cards"]


def test_unicode_numbers_are_normalized_but_unknown_values_still_fail():
    pack = {
        "facts": {"selected_period": "2026-10"},
        "metrics": {"contribution": {"value": "50.00", "unit": "INR"}},
    }
    result = chat.canonical_reply("𝗢𝗰𝘁𝗼𝗯𝗲𝗿 𝟮𝟬𝟮𝟲: ５０.００ INR", pack)
    assert result == "{{selected_period}}: {{contribution}}"
    assert "999" in chat.canonical_reply("９９９ INR", pack)
