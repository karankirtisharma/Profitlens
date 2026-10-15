"""Offline deployment checks: no real cloud credentials or document transfers."""

import json
from pathlib import Path

import httpx2
import pytest
from fastapi.testclient import TestClient
from profitlens import storage
from profitlens.config import Settings, settings
from profitlens.main import app
from pydantic import SecretStr, ValidationError

KEY = "00000000-0000-0000-0000-000000000001.pdf"


def hosted(**overrides):
    return Settings(
        _env_file=None,
        **(
            {
                "vercel": True,
                "database_url": "postgresql+psycopg://user:fake@db.invalid/demo?sslmode=require",
                "database_pool_mode": "null",
                "web_origin": "https://demo.example.test",
                "cookie_secure": True,
                "storage_backend": "vercel_blob",
                "blob_read_write_token": "test-placeholder",
                "blob_store_id": "teststore",
                "upload_limit_bytes": 4_000_000,
                "ai_timeout_seconds": 20,
            }
            | overrides
        ),
    )


@pytest.mark.parametrize(
    "change",
    [
        {"cookie_secure": False},
        {"web_origin": "http://demo.example.test"},
        {"web_origin": "https://demo.example.test/path"},
        {"storage_backend": "local"},
        {"database_pool_mode": "queue"},
        {"upload_limit_bytes": 5_000_000},
        {"ai_timeout_seconds": 60},
        {"blob_read_write_token": ""},
        {"database_url": "postgresql+psycopg://user:fake@db.invalid/demo"},
    ],
)
def test_unsafe_hosted_settings_are_rejected(change):
    with pytest.raises(ValidationError):
        hosted(**change)


def test_local_and_hosted_upload_limits():
    local = Settings(_env_file=None)
    assert local.file_limit("csv") == 5 * 1024 * 1024
    assert local.file_limit("pdf") == 10 * 1024 * 1024
    assert hosted().file_limit("pdf") == 4_000_000
    assert hosted().request_limit < 4_500_000


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+psycopg"])
def test_provider_database_urls_preserve_credentials_and_tls(scheme):
    suffix = (
        "user:p%40ss%2Fword@db.invalid/demo?sslmode=require&channel_binding=require"
    )
    configured = hosted(database_url=f"{scheme}://{suffix}")
    assert configured.database_url == f"postgresql+psycopg://{suffix}"
    with pytest.raises(ValidationError):
        hosted(database_url=f"{scheme}://user:fake@db.invalid/demo?sslmode=disable")


def test_config_and_liveness_do_not_need_database(monkeypatch):
    monkeypatch.setattr(settings, "upload_limit_bytes", 4_000_000)
    client = TestClient(app)
    assert client.get("/api/live").json() == {"status": "ok"}
    response = client.get("/api/config")
    assert response.json() == {"csv_max_bytes": 4_000_000, "pdf_max_bytes": 4_000_000}
    assert response.headers["cache-control"] == "no-store"


def test_local_storage_cannot_overwrite_or_escape(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    monkeypatch.setattr(settings, "storage_backend", "local")
    storage.put("demo-org", KEY, b"fixture")
    assert storage.read("demo-org", KEY) == b"fixture"
    with pytest.raises(FileExistsError):
        storage.put("demo-org", KEY, b"different")
    for org, key in [
        ("../other", KEY),
        ("demo-org", "../file.pdf"),
        ("demo-org", "https://example.test/file.pdf"),
    ]:
        with pytest.raises(storage.StorageUnavailable):
            storage.read(org, key)
    storage.remove("demo-org", KEY)
    with pytest.raises(FileNotFoundError):
        storage.read("demo-org", KEY)


@pytest.fixture
def blob_transport(monkeypatch):
    """Run the actual installed SDK against a local HTTP mock, not a cloud service."""
    monkeypatch.setattr(settings, "storage_backend", "vercel_blob")
    monkeypatch.setattr(settings, "blob_store_id", "teststore")
    token = "vercel_blob_rw_" + "teststore_offline-fixture"
    monkeypatch.setattr(settings, "blob_read_write_token", SecretStr(token))
    original_client = httpx2.Client
    calls = []
    content = b"%PDF offline fixture"
    name = f"demo-org/{KEY}"
    url = f"https://teststore.private.blob.vercel-storage.com/{name}"

    def handler(request):
        calls.append(request)
        assert request.headers["authorization"] == f"Bearer {token}"
        if request.method == "PUT":
            assert request.headers["x-vercel-blob-access"] == "private"
            assert request.headers["x-allow-overwrite"] == "0"
            assert request.headers["x-add-random-suffix"] == "0"
            assert request.content == content
            return httpx2.Response(
                200,
                json={
                    "url": url,
                    "downloadUrl": url,
                    "pathname": name,
                    "contentType": "application/pdf",
                    "contentDisposition": "attachment",
                    "etag": "test-etag",
                },
            )
        if request.method == "GET":
            assert str(request.url) == url
            return httpx2.Response(
                200, content=content, headers={"Content-Type": "application/pdf"}
            )
        return httpx2.Response(200, json={})

    class MockClient(original_client):
        def __init__(self, **kwargs):
            super().__init__(transport=httpx2.MockTransport(handler), **kwargs)

    monkeypatch.setattr(storage.httpx2, "Client", MockClient)
    return calls, content


def test_private_blob_sdk_roundtrip(blob_transport):
    calls, content = blob_transport
    storage.put("demo-org", KEY, content)
    assert storage.read("demo-org", KEY) == content
    storage.remove("demo-org", KEY)
    assert len(calls) == 3


def test_cloud_download_size_is_bounded(blob_transport, monkeypatch):
    monkeypatch.setattr(settings, "upload_limit_bytes", 3)
    with pytest.raises(storage.StorageUnavailable, match="download limit"):
        storage.read("demo-org", KEY)


def test_deployment_pins_and_entrypoint():
    root = Path(__file__).resolve().parents[1]
    locked = set((root / "requirements.lock").read_text().splitlines())
    runtime = (root / "apps/api/requirements.txt").read_text().splitlines()
    assert all(line in locked for line in runtime if line and not line.startswith("#"))
    api = json.loads((root / "apps/api/vercel.json").read_text())
    web = json.loads((root / "apps/web/vercel.json").read_text())
    assert api["framework"] == "fastapi" and web["framework"] == "nextjs"
    assert api["functions"]["index.py"]["maxDuration"] < 120
    assert (root / "apps/api/index.py").is_file()
