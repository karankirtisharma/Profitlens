"""Provider protocol tests use HTTP mocks, never external APIs or real credentials."""

import json

import httpx
import pytest
from profitlens import explanations
from profitlens.config import settings
from pydantic import SecretStr


@pytest.mark.parametrize(
    "provider,host",
    [("openrouter", "openrouter.ai"), ("nvidia", "integrate.api.nvidia.com")],
)
def test_provider_protocol_and_strict_schema(monkeypatch, provider, host):
    monkeypatch.setattr(settings, "ai_provider", provider)
    monkeypatch.setattr(settings, "ai_model", "test-model")
    monkeypatch.setattr(settings, "openrouter_api_key", SecretStr("test-key"))
    monkeypatch.setattr(settings, "nvidia_api_key", SecretStr("test-key"))
    real_client = httpx.Client

    def respond(request):
        assert request.url.host == host
        assert request.headers["Authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["response_format"]["json_schema"]["strict"] is True
        assert "test-key" not in request.content.decode()
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "insufficient_evidence": True,
                                    "metrics": [],
                                    "finding_ids": [],
                                    "citations": [],
                                }
                            )
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(
        explanations.httpx,
        "Client",
        lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs),
    )
    assert explanations.generate({"question": "test"}).insufficient_evidence


@pytest.mark.parametrize("failure", ["http", "malformed", "oversize", "timeout"])
def test_provider_failure_hides_body_and_credentials(monkeypatch, failure):
    monkeypatch.setattr(settings, "ai_provider", "openrouter")
    monkeypatch.setattr(settings, "ai_model", "test-model")
    monkeypatch.setattr(settings, "openrouter_api_key", SecretStr("test-key"))
    real_client = httpx.Client

    def respond(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("Private provider details", request=request)
        return httpx.Response(
            500 if failure == "http" else 200,
            text="private payload" if failure != "oversize" else "x" * 70000,
        )

    monkeypatch.setattr(
        explanations.httpx,
        "Client",
        lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs),
    )
    with pytest.raises(explanations.ProviderError) as exc:
        explanations.generate({"question": "test"})
    assert "private" not in str(exc.value) and "test-key" not in str(exc.value)
