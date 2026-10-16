"""Chat boundary tests: mocked model, real isolated database and permissions."""

import pytest
from profitlens import chat, explanations
from profitlens import database as db
from sqlalchemy import delete
from test_analysis import ready, setup
from test_workspace import BASE, TEST_URL, client, pdf, upload
from test_workspace import fixture_data as fixture_data
from test_workspace import hash_password as hash_password
from test_workspace import migrated_database as migrated_database

pytestmark = pytest.mark.skipif(not TEST_URL, reason="Dedicated test DB required")


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(explanations, "provider_status", lambda: {"configured": True})


def answer(pack, **changes):
    return chat.ChatAnswer(
        **(
            {
                "reply": "Recorded contribution is {{contribution}}. This is not net profit.",
                "insufficient_evidence": False,
                "finding_ids": [],
                "source_ids": [],
            }
            | changes
        )
    )


def ask(c, **changes):
    return c.post(
        BASE + "/chat",
        json={
            "customer_id": "C1",
            "billing_period": "2026-09",
            "message": "What is the contribution?",
            **changes,
        },
    )


def test_chat_real_financial_data_and_bounded_followup(monkeypatch):
    c = client()
    setup(c)
    captured = []

    def model(schema, prompt, payload, max_tokens):
        captured.append(payload)
        assert max_tokens == 900
        assert "invoice_lines" not in payload["CURRENT_EVIDENCE"]
        return answer(payload["CURRENT_EVIDENCE"])

    monkeypatch.setattr(explanations, "structured_completion", model)
    first = ask(c)
    assert first.status_code == 200, first.text
    assert "50.00 INR" in first.json()["reply"]
    assert first.json()["profitability_status"] == "provisional"
    assert first.json()["record_ids"] == {"invoices": ["I"], "expenses": ["E"]}
    second = ask(
        c,
        message="Explain that more simply",
        history=[
            {"role": "user", "content": "What is the contribution?"},
            {"role": "assistant", "content": first.json()["reply"]},
        ],
    )
    assert second.status_code == 200
    assert len(captured[-1]["recent_conversation"]) == 2


def test_chat_contract_citations_from_current_authorized_evidence(monkeypatch):
    c = client()
    ready(c)

    def model(schema, prompt, payload, max_tokens):
        pack = payload["CURRENT_EVIDENCE"]
        p = pack["passages"][0]
        return answer(
            pack,
            reply="The agreement includes service delivery and support.",
            source_ids=[p["source_id"]],
        )

    monkeypatch.setattr(explanations, "structured_completion", model)
    r = ask(c, message="What does the service delivery support contract cover?")
    assert r.status_code == 200, r.text
    assert r.json()["sources"][0]["source_url"].startswith(BASE + "/contracts/")


@pytest.mark.parametrize(
    "change",
    [
        {"reply": "Contribution is 999999 INR."},
        {"reply": "Contribution is {{invented}}."},
        {"finding_ids": ["foreign-finding"]},
        {"source_ids": ["foreign"]},
    ],
)
def test_chat_rejects_fabricated_values_or_sources(monkeypatch, change):
    c = client()
    setup(c)
    monkeypatch.setattr(
        explanations,
        "structured_completion",
        lambda schema, prompt, payload, **kw: answer(
            payload["CURRENT_EVIDENCE"], **change
        ),
    )
    r = ask(c)
    assert r.status_code == 502
    assert "999999" not in r.text


def test_chat_authorization_precedes_provider(monkeypatch):
    monkeypatch.setattr(
        explanations,
        "structured_completion",
        lambda *a, **k: pytest.fail("Unauthorized provider call"),
    )
    assert ask(client("analyst"), customer_id="C2").status_code == 404
    assert ask(client("outsider")).status_code == 404


def test_chat_rechecks_permissions_after_provider(monkeypatch):
    c = client()
    setup(c)
    analyst = client("analyst")

    def revoke(schema, prompt, payload, **kw):
        with db.engine.begin() as conn:
            conn.execute(delete(db.grants))
        return answer(payload["CURRENT_EVIDENCE"])

    monkeypatch.setattr(explanations, "structured_completion", revoke)
    assert ask(analyst).status_code == 404


def test_chat_rechecks_changed_data(monkeypatch):
    c = client()
    setup(c)

    def changed(schema, prompt, payload, **kw):
        with db.engine.begin() as conn:
            conn.execute(db.expenses.update().values(amount=99))
        return answer(payload["CURRENT_EVIDENCE"])

    monkeypatch.setattr(explanations, "structured_completion", changed)
    assert ask(c).status_code == 409


def test_chat_no_canned_fallback_when_provider_unavailable(monkeypatch):
    c = client()
    monkeypatch.setattr(explanations, "provider_status", lambda: {"configured": False})
    assert ask(c, customer_id=None).status_code == 503


def test_general_conversation_and_insufficient_evidence_use_provider(monkeypatch):
    c = client()
    called = []

    def model(schema, prompt, payload, **kw):
        called.append(payload)
        assert "contribution" not in payload["CURRENT_EVIDENCE"]["metrics"]
        return chat.ChatAnswer(
            reply="No financial records are available for this month.",
            insufficient_evidence=True,
            finding_ids=[],
            source_ids=[],
        )

    monkeypatch.setattr(explanations, "structured_completion", model)
    result = ask(c, customer_id=None, message="How is my business doing?")
    assert result.status_code == 200
    assert called and result.json()["insufficient_evidence"]


def test_manual_greeting_hides_unrelated_financial_panels(monkeypatch):
    c = client()
    setup(c)

    def model(schema, prompt, payload, **kw):
        assert "conversational" in schema.model_json_schema()["required"]
        return chat.ChatAnswer(
            reply="Hi! I'm your ProfitLens assistant. How can I help?",
            conversational=True,
            insufficient_evidence=False,
            finding_ids=[],
            source_ids=[],
        )

    monkeypatch.setattr(explanations, "structured_completion", model)
    result = ask(c, message="hi")
    assert result.status_code == 200
    data = result.json()
    assert data["billing_period"] is None and data["scope_label"] is None
    assert (
        not data["cards"] and not data["actions"] and not data["insufficient_evidence"]
    )


def test_chat_limits_input_and_rate(monkeypatch):
    c = client()
    assert ask(c, message=" ").status_code == 422
    assert ask(c, history=[{"role": "user", "content": "hi"}] * 7).status_code == 422
    monkeypatch.setattr(
        explanations,
        "structured_completion",
        lambda *a, **kw: chat.ChatAnswer(
            reply="Hello, how can I help?",
            insufficient_evidence=False,
            source_ids=[],
            finding_ids=[],
        ),
    )
    for _ in range(20):
        assert ask(c, customer_id=None, message="Hello").status_code == 200
    assert ask(c, customer_id=None, message="Hello").status_code == 429


@pytest.mark.parametrize(
    "reply,expected",
    [
        ("Contribution is INR 50 and margin is {{margin_percent}}.", 200),
        ("Contribution is USD 50.", 502),
        ("Contribution is INR 50.01.", 502),
    ],
)
def test_chat_literal_amounts_require_exact_unit_and_value(
    monkeypatch, reply, expected
):
    c = client()
    setup(c)
    monkeypatch.setattr(
        explanations,
        "structured_completion",
        lambda schema, prompt, payload, **kw: answer(
            payload["CURRENT_EVIDENCE"], reply=reply
        ),
    )
    result = ask(c)
    assert result.status_code == expected
    if expected == 200:
        assert "50.00 INR" in result.json()["reply"]


def test_unreviewed_pdf_can_be_summarized_without_financial_records(monkeypatch):
    c = client()
    upload(c, "C1", pdf("Service agreement. Monthly support and maintenance included."))

    def model(schema, prompt, payload, **kw):
        pack = payload["CURRENT_EVIDENCE"]
        assert pack["documents"][0]["evidence_status"] == "unreviewed"
        assert pack["passages"] and pack["metrics"] == {}
        return answer(
            pack,
            reply="This uploaded agreement includes monthly support. Its terms still need review.",
            source_ids=[pack["passages"][0]["source_id"]],
        )

    monkeypatch.setattr(explanations, "structured_completion", model)
    r = ask(c, billing_period=None, message="Summarize my uploaded document")
    assert r.status_code == 200, r.text
    assert r.json()["sources"][0]["evidence_status"] == "unreviewed"
    assert r.json()["profitability_status"] == "no_records"


def test_old_month_retains_reference_document_and_actual_date_facts(monkeypatch):
    c = client()
    ready(c)

    def model(schema, prompt, payload, **kw):
        pack = payload["CURRENT_EVIDENCE"]
        assert pack["documents"][0]["evidence_status"] == "outside_selected_period"
        assert pack["available_periods"] == ["2026-09"]
        assert "contribution" not in pack["metrics"]
        return answer(
            pack,
            reply="1. No financial records for February 2026.\n2. This agreement begins on 1 September 2026; select September 2026 for financial data.",
            source_ids=[pack["passages"][0]["source_id"]],
        )

    monkeypatch.setattr(explanations, "structured_completion", model)
    r = ask(c, billing_period="2026-02", message="Tell me about the contract")
    assert r.status_code == 200, r.text
    assert "2026-02" in r.json()["reply"]
    assert "2026-09-01" in r.json()["reply"]
    assert "select 2026-09 for financial data" in r.json()["reply"]
    assert r.json()["sources"][0]["evidence_status"] == "outside_selected_period"


def test_unknown_date_still_rejected(monkeypatch):
    c = client()
    ready(c)
    monkeypatch.setattr(
        explanations,
        "structured_completion",
        lambda schema, prompt, payload, **kw: answer(
            payload["CURRENT_EVIDENCE"], reply="This contract ends on 2099-01-01."
        ),
    )
    assert ask(c).status_code == 502


def test_unreviewed_document_quotes_do_not_become_financial_metrics(monkeypatch):
    c = client()
    upload(
        c,
        "C1",
        pdf(
            "Effective period: 01 September 2026 to 28 February 2027. Monthly charge INR 20000.00. Payment within 30 days."
        ),
    )

    def model(schema, prompt, payload, **kw):
        pack = payload["CURRENT_EVIDENCE"]
        assert pack["metrics"] == {}
        return answer(
            pack,
            reply="1. The uploaded document runs from September 2026 to February 2027.\n2. It states INR 20000.00 and payment within 30 days; it is unreviewed.",
            source_ids=[pack["passages"][0]["source_id"]],
        )

    monkeypatch.setattr(explanations, "structured_completion", model)
    r = ask(c, billing_period="2026-02")
    assert r.status_code == 200, r.text
    assert r.json()["metrics"] == []
    assert "not validated pricing" in r.json()["reply"]
    assert r.json()["sources"][0]["evidence_status"] == "unreviewed"
    assert "from 2026-09 to 2027-02" in r.json()["reply"]


def test_source_chat_totals_citations_and_permissions(monkeypatch):
    c = client()
    data = b"date,amount,customer,description\n2026-09-01,100,C1,Service\n2026-09-02,-20,C1,Credit\n2026-09-03,900,C2,Restricted\n"
    doc = c.post(BASE + "/sources", files={"file": ("sales.csv", data)}).json()
    mapping = {
        "kind": "reported_sales",
        "columns": {
            "date": "date",
            "amount": "amount",
            "customer_id": "customer",
            "description": "description",
        },
        "currency": "INR",
    }
    preview = c.post(BASE + f"/sources/{doc['id']}/preview", json=mapping).json()
    assert not preview["issues"]
    assert (
        c.post(
            BASE + f"/sources/{doc['id']}/confirm",
            json={"preview_token": preview["preview_token"]},
        ).status_code
        == 200
    )
    seen = []

    def model(schema, prompt, payload, max_tokens):
        evidence = payload["CURRENT_EVIDENCE"]
        seen.append(evidence)
        assert evidence["metrics"]["source_a_amount"]["value"] == "80.00"
        assert "Restricted" not in str(evidence)
        return answer(
            evidence,
            reply="Reported sales are {{source_a_amount}}; profit cannot be established.",
            source_ids=[],
        )

    monkeypatch.setattr(explanations, "structured_completion", model)
    r = ask(client("analyst"), message="Explain sales")
    assert r.status_code == 200, r.text
    out = r.json()
    assert "80.00 INR" in out["reply"]
    assert out["sources"] and "customer_id=C1" in out["sources"][0]["source_url"]
    assert (
        client("analyst")
        .get(out["sources"][0]["source_url"])
        .json()["groups"][0]["amount"]
        == "80.00"
    )
    assert client("outsider").get(out["sources"][0]["source_url"]).status_code == 404
    assert out["actions"][0]["view"] == "data"
    assert "contribution" not in seen[0]["metrics"]


def test_source_chat_rejects_fabricated_amount(monkeypatch):
    from profitlens.security import scope
    from profitlens.source_chat import enrich

    c = client()
    doc = c.post(
        BASE + "/sources", files={"file": ("cost.csv", b"amount\n42\n")}
    ).json()
    p = c.post(
        BASE + f"/sources/{doc['id']}/preview",
        json={
            "kind": "expenditure",
            "columns": {"amount": "amount"},
            "currency": "INR",
        },
    ).json()
    c.post(
        BASE + f"/sources/{doc['id']}/confirm",
        json={"preview_token": p["preview_token"]},
    )
    with db.engine.begin() as conn:
        s = scope("a", {"id": "admin"}, conn)
        payload = chat.ChatRequest(message="What is profit?")
        pack = enrich(conn, s, chat.evidence(conn, s, payload), True)
    monkeypatch.setattr(
        explanations,
        "structured_completion",
        lambda *a, **k: answer({}, reply="Profit is INR 999.00."),
    )
    with pytest.raises(Exception) as err:
        chat.respond(pack, payload)
    assert err.value.status_code == 502
    assert all(
        "profit" not in key and "contribution" not in key for key in pack["metrics"]
    )
