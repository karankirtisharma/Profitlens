"""New roadmap integration tests use an isolated PostgreSQL database."""

from decimal import Decimal

import pytest
from profitlens import database as db
from profitlens import explanations
from profitlens.config import settings
from profitlens.explanations import Citation, MetricClaim, ModelAnswer
from pydantic import SecretStr
from sqlalchemy import delete
from test_workspace import (
    BASE,
    TERMS,
    TEST_URL,
    client,
    invoice,
    pdf,
    upload,
)
from test_workspace import (
    fixture_data as fixture_data,
)
from test_workspace import (
    hash_password as hash_password,
)
from test_workspace import (
    migrated_database as migrated_database,
)

pytestmark = pytest.mark.skipif(
    not TEST_URL, reason="Dedicated PostgreSQL test DB required"
)


def setup(c, customer="C1", cost="40.00", period="2026-09", suffix=""):
    assert (
        c.post(
            BASE + "/records/invoices",
            json=invoice("I" + suffix, customer, billing_period=period),
        ).status_code
        == 201
    )
    assert (
        c.post(
            BASE + "/records/expenses",
            json={
                "expense_id": "E" + suffix,
                "customer_id": customer,
                "billing_period": period,
                "currency": "INR",
                "category": "Service delivery",
                "amount": cost,
            },
        ).status_code
        == 201
    )


def item(c, customer="C1", period="2026-09"):
    r = c.get(
        BASE + "/profitability",
        params={"customer_id": customer, "billing_period": period},
    )
    assert r.status_code == 200, r.text
    return r.json()["items"][0]


def confirm(c, customer="C1", period="2026-09"):
    current = item(c, customer, period)
    return c.put(
        BASE + f"/profitability/{customer}/{period}/cost-review",
        json={
            "input_hash": current["cost_input_hash"],
            "note": "All direct costs reviewed against the source ledger.",
        },
    )


def ready(c, customer="C1", suffix=""):
    setup(c, customer, suffix=suffix)
    document = upload(
        c,
        customer,
        pdf(
            "Service delivery monthly contract. Support and maintenance included. Monthly rate INR 100."
        ),
    )
    assert (
        c.put(BASE + f"/contracts/{document['id']}/terms", json=TERMS).status_code
        == 200
    )
    assert confirm(c, customer).status_code == 200
    return document


def ask(c, customer="C1"):
    return c.post(
        BASE + "/investigations",
        json={
            "customer_id": customer,
            "billing_period": "2026-09",
            "question": "What is the service delivery margin and monthly support contract?",
        },
    )


def valid_answer(pack):
    p = pack["passages"][0]
    return ModelAnswer(
        insufficient_evidence=False,
        metrics=[
            MetricClaim(metric_id="contribution", **pack["metrics"]["contribution"])
        ],
        finding_ids=[f["id"] for f in pack["findings"]],
        citations=[Citation(source_id=p["source_id"], quote=p["content"])],
    )


def test_contribution_cost_attestation_and_stale_updates():
    c = client()
    setup(c)
    row = item(c)
    assert (
        row["contribution"],
        row["margin_percent"],
        row["profitability_status"],
    ) == ("50.00", "55.56", "provisional")
    assert confirm(c).status_code == 200
    assert item(c)["profitability_status"] == "confirmed"
    updated = {
        "expense_id": "E",
        "customer_id": "C1",
        "billing_period": "2026-09",
        "currency": "INR",
        "category": "Service delivery",
        "amount": "50.00",
    }
    assert c.put(BASE + "/records/expenses/E", json=updated).status_code == 200
    changed = item(c)
    assert changed["completeness"] == "stale" and changed["contribution"] == "40.00"
    assert (
        c.put(
            BASE + "/profitability/C1/2026-09/cost-review",
            json={
                "input_hash": row["cost_input_hash"],
                "note": "All source costs were reviewed.",
            },
        ).status_code
        == 409
    )


def test_zero_missing_costs_and_analyst_write_denied():
    c = client()
    assert (
        c.post(
            BASE + "/records/invoices",
            json=invoice(subtotal="0", discount="0", tax="0", total="0"),
        ).status_code
        == 201
    )
    assert item(c)["contribution"] is None
    assert confirm(c).status_code == 409
    c.post(
        BASE + "/records/expenses",
        json={
            "expense_id": "E",
            "customer_id": "C1",
            "billing_period": "2026-09",
            "category": "Explicit zero",
            "amount": "0",
            "currency": "INR",
        },
    )
    row = item(c)
    assert row["contribution"] == "0.00" and row["margin_percent"] is None
    assert confirm(client("analyst")).status_code == 403


def test_discrepancies_and_thresholds_require_review():
    c = client()
    ready(c)
    setup(c, cost="20.00", period="2026-08", suffix="prior")
    assert [f["rule"] for f in item(c)["findings"]] == ["pricing_mismatch"]
    assert confirm(c, period="2026-08").status_code == 200
    assert {f["rule"] for f in item(c)["findings"]} == {
        "pricing_mismatch",
        "cost_increase",
        "margin_decline",
    }
    r = c.get(
        BASE + "/profitability",
        params={
            "customer_id": "C1",
            "billing_period": "2026-09",
            "cost_increase_percent": 200,
            "margin_decline_points": 50,
            "pricing_tolerance": 20,
        },
    )
    assert r.json()["items"][0]["findings"] == []
    assert c.get(BASE + "/profitability?cost_increase_percent=NaN").status_code == 422


def test_refunds_do_not_create_price_mismatch():
    c = client()
    ready(c)
    c.put(
        BASE + "/records/invoices/I",
        json=invoice(
            "I", subtotal="100", discount="0", refund="30", tax="9", total="79"
        ),
    ).raise_for_status()
    row = item(c)
    assert row["net_billed_revenue"] == "70.00" and row["findings"] == []


def test_retrieval_scopes_period_and_page_provenance():
    c = client()
    doc = ready(c)
    ready(c, "C2", "secret")
    analyst = client("analyst")
    params = {"customer_id": "C1", "billing_period": "2026-09", "q": "monthly support"}
    result = analyst.get(BASE + "/evidence/search", params=params).json()
    assert result["items"][0]["contract_id"] == doc["id"]
    assert result["items"][0]["page"] == 1 and "file_key" not in result["items"][0]
    assert (
        analyst.get(
            BASE + "/evidence/search", params=params | {"customer_id": "C2"}
        ).status_code
        == 404
    )
    assert (
        client("outsider").get(BASE + "/evidence/search", params=params).status_code
        == 404
    )
    assert (
        analyst.get(
            BASE + "/evidence/search", params=params | {"billing_period": "2026-08"}
        ).json()["items"]
        == []
    )
    assert analyst.get(
        BASE + "/evidence/search",
        params=params | {"billing_period": "2026-08", "mode": "baseline"},
    ).json()["items"]
    assert analyst.post(BASE + "/evidence/reindex").status_code == 403
    assert c.post(BASE + "/evidence/reindex").json()["documents"] == 2


def test_verified_investigation_history_and_revocation(monkeypatch):
    c = client()
    ready(c)
    monkeypatch.setattr(explanations, "generate", valid_answer)
    analyst = client("analyst")
    r = ask(analyst)
    assert r.status_code == 201, r.text
    assert r.json()["result"]["status"] == "verified"
    identifier = r.json()["id"]
    assert analyst.get(BASE + "/investigations/" + identifier).json()["stale"] is False
    c.put(BASE + "/members/analyst/customers", json={"customer_ids": []})
    assert analyst.get(BASE + "/investigations/" + identifier).status_code == 404
    assert analyst.get(BASE + "/investigations").json() == []


@pytest.mark.parametrize("failure", ["number", "source", "quote", "finding"])
def test_unsupported_model_claims_are_withheld(monkeypatch, failure):
    c = client()
    ready(c)

    def invalid(pack):
        a = valid_answer(pack)
        if failure == "number":
            a.metrics[0].value = "999999.00"
        if failure == "source":
            a.citations[0].source_id = "passage:secret"
        if failure == "quote":
            a.citations[0].quote = "A made up claim not present in the document."
        if failure == "finding":
            a.finding_ids = ["other-tenant:profit"]
        return a

    monkeypatch.setattr(explanations, "generate", invalid)
    result = ask(c).json()["result"]
    assert result["status"] == "rejected" and result["answer"] is None


def test_insufficient_evidence_does_not_call_provider(monkeypatch):
    c = client()
    setup(c)

    def unexpected(_):
        raise AssertionError("Should not call the provider")

    monkeypatch.setattr(explanations, "generate", unexpected)
    assert ask(c).json()["result"]["status"] == "insufficient_evidence"


def test_provider_failure_is_explicit_and_secret_not_in_status(monkeypatch):
    c = client()
    ready(c)
    monkeypatch.setattr(
        settings, "openrouter_api_key", SecretStr("test-not-a-real-key")
    )

    def offline(_):
        raise explanations.ProviderError("provider_unavailable_or_invalid_output")

    monkeypatch.setattr(explanations, "generate", offline)
    assert ask(c).json()["result"]["status"] == "provider_unavailable"
    assert "test-not-a-real-key" not in c.get(BASE + "/ai/status").text


def test_edit_during_generation_and_stale_history(monkeypatch):
    c = client()
    ready(c)
    monkeypatch.setattr(explanations, "generate", valid_answer)
    identifier = ask(c).json()["id"]

    def changed(pack):
        with db.engine.begin() as conn:
            conn.execute(
                db.expenses.update()
                .where(db.expenses.c.organization_id == "a")
                .values(amount=Decimal("45"))
            )
        return valid_answer(pack)

    monkeypatch.setattr(explanations, "generate", changed)
    assert ask(c).status_code == 409
    result = c.get(BASE + "/investigations/" + identifier).json()
    assert result["stale"] and result["result"] is None


def test_grant_revoked_during_generation_returns_no_output(monkeypatch):
    c = client()
    ready(c)
    analyst = client("analyst")

    def revoked(pack):
        with db.engine.begin() as conn:
            conn.execute(delete(db.grants))
        return valid_answer(pack)

    monkeypatch.setattr(explanations, "generate", revoked)
    assert ask(analyst).status_code == 404


def scoped_ask(c, scope, question="What is the recorded revenue for this month?"):
    return c.post(
        BASE + "/investigations",
        json={
            "customer_id": "C1",
            "billing_period": "2026-09",
            "question": question,
            "evidence_scope": scope,
        },
    )


def revenue_answer(pack):
    return ModelAnswer(
        insufficient_evidence=False,
        metrics=[
            MetricClaim(
                metric_id="net_billed_revenue", **pack["metrics"]["net_billed_revenue"]
            )
        ],
        finding_ids=[],
        citations=[],
    )


def test_revenue_only_investigation_without_costs_or_contract(monkeypatch):
    c = client()
    c.post(BASE + "/records/invoices", json=invoice()).raise_for_status()
    monkeypatch.setattr(explanations, "generate", revenue_answer)
    response = scoped_ask(c, "financial")
    assert response.status_code == 201
    data = response.json()
    assert data["result"]["status"] == "verified"
    assert data["evidence"]["passages"] == []
    assert "contribution" not in data["evidence"]["metrics"]
    assert "90.00 INR" in data["result"]["summary"]
    assert "Cost coverage is not confirmed" in " ".join(data["result"]["limitations"])
    detail = c.get(BASE + "/investigations/" + data["id"]).json()
    assert detail["stale"] is False
    assert detail["evidence"]["evidence_scope"] == "financial"
    assert scoped_ask(client("outsider"), "financial").status_code == 404


def test_contract_only_question_needs_no_invoice_or_cost(monkeypatch):
    c = client()
    doc = upload(
        c,
        "C1",
        pdf("Monthly service support agreement includes maintenance and support."),
    )
    c.put(BASE + f"/contracts/{doc['id']}/terms", json=TERMS).raise_for_status()

    def answer(pack):
        assert pack["metrics"] == {} and pack["invoice_lines"] == []
        p = pack["passages"][0]
        return ModelAnswer(
            insufficient_evidence=False,
            metrics=[],
            finding_ids=[],
            citations=[Citation(source_id=p["source_id"], quote=p["content"])],
        )

    monkeypatch.setattr(explanations, "generate", answer)
    response = scoped_ask(
        c, "contract", "What monthly maintenance and support is covered?"
    )
    assert response.status_code == 201
    assert response.json()["result"]["status"] == "verified"


def test_unreviewed_contract_and_empty_financial_scope_do_not_call_provider(
    monkeypatch,
):
    c = client()
    upload(c, "C1", pdf())

    def unexpected(_):
        raise AssertionError("No usable evidence must not call the model")

    monkeypatch.setattr(explanations, "generate", unexpected)
    for scope in ("contract", "financial", "combined"):
        assert (
            scoped_ask(c, scope).json()["result"]["status"] == "insufficient_evidence"
        )
    assert scoped_ask(c, "unknown").status_code == 422


def test_provisional_contribution_is_labelled_and_contract_claims_rejected(monkeypatch):
    c = client()
    setup(c)

    def provisional(pack):
        return ModelAnswer(
            insufficient_evidence=False,
            metrics=[
                MetricClaim(metric_id="contribution", **pack["metrics"]["contribution"])
            ],
            finding_ids=[],
            citations=[],
        )

    monkeypatch.setattr(explanations, "generate", provisional)
    result = scoped_ask(c, "financial").json()["result"]
    assert result["status"] == "verified"
    assert result["summary"].startswith("Provisional Contribution: 50.00 INR")

    def fabricated(pack):
        answer = provisional(pack)
        answer.citations = [
            Citation(
                source_id="passage:invented", quote="An invented monthly contract rate."
            )
        ]
        return answer

    monkeypatch.setattr(explanations, "generate", fabricated)
    assert scoped_ask(c, "financial").json()["result"]["status"] == "rejected"


def test_combined_requires_both_evidence_types_but_not_cost_attestation(monkeypatch):
    c = client()
    ready(c)
    with db.engine.begin() as conn:
        conn.execute(delete(db.cost_reviews))
    monkeypatch.setattr(explanations, "generate", valid_answer)
    assert ask(c).json()["result"]["status"] == "verified"
    monkeypatch.setattr(explanations, "generate", revenue_answer)
    result = ask(c).json()["result"]
    assert result["status"] == "rejected"
    assert "missing_evidence" in result["verification_errors"]
