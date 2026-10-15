import pytest
from profitlens import evaluation, retrieval
from profitlens.explanations import Citation, MetricClaim, ModelAnswer, verify
from pydantic import ValidationError


def test_chunking_preserves_pages_and_stable_ids():
    contract = {
        "id": "doc",
        "organization_id": "a",
        "customer_id": "C1",
        "pages": [
            {"page": 2, "text": "alpha " * 600},
            {"page": 4, "text": "Support applies monthly."},
        ],
    }
    chunks = list(retrieval.chunks(contract))
    assert chunks == list(retrieval.chunks(contract))
    assert {c["page"] for c in chunks} == {2, 4}
    assert all(len(c["content"]) <= 1200 for c in chunks)
    assert len({c["id"] for c in chunks}) == len(chunks)
    assert retrieval.rank("zzzzzz", chunks) == []
    assert retrieval.rank("support", chunks)[0]["page"] == 4


def test_frozen_evaluation_corpus_and_calculation_labels():
    assert evaluation.dataset() == evaluation.dataset()
    result = evaluation.benchmark()
    assert result["counts"]["questions"] == 30
    assert result["financial"]["contribution_correct"] == 20
    assert result["financial"]["false_positive"] == 0
    assert result["financial"]["false_negative"] == 0
    assert result["retrieval"]["context"]["summary"]["held_out"]["answerable"] == 15
    # Keep known lexical failure visible: do not tune fixtures to claim perfect retrieval.
    assert result["retrieval"]["context"]["summary"]["held_out"]["recall_at_3"] < 1


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", "12x", "999.00"])
def test_verifier_rejects_nonfinite_or_wrong_numbers(value):
    a = ModelAnswer(
        insufficient_evidence=False,
        metrics=[MetricClaim(metric_id="contribution", value=value, unit="INR")],
        finding_ids=[],
        citations=[
            Citation(source_id="passage:1", quote="The monthly service is covered.")
        ],
    )
    pack = {
        "metrics": {"contribution": {"value": "50.00", "unit": "INR"}},
        "findings": [],
        "passages": [
            {"source_id": "passage:1", "content": "The monthly service is covered."}
        ],
    }
    assert "unsupported_metric" in verify(a, pack)


def test_model_schema_rejects_unchecked_prose():
    with pytest.raises(ValidationError):
        ModelAnswer.model_validate(
            {
                "insufficient_evidence": False,
                "metrics": [],
                "finding_ids": [],
                "citations": [],
                "summary": "Invented savings of one million!",
            }
        )
