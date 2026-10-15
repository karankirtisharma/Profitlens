"""Private PDF persistence. Authorization belongs to the calling API route."""

import re
from contextlib import contextmanager

import httpx2
from vercel.api import session
from vercel.blob import sync as blob

from .config import settings


class StorageUnavailable(Exception):
    """Safe public error without provider credentials, URLs or response bodies."""


def object_name(organization_id: str, key: str) -> str:
    # These are database identifiers, never a browser-supplied path or URL.
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,36}", organization_id) or not re.fullmatch(
        r"[a-f0-9-]{36}\.pdf", key
    ):
        raise StorageUnavailable("Invalid private file reference")
    return f"{organization_id}/{key}"


@contextmanager
def cloud():
    options = blob.SyncBlobServiceOptions(
        credentials_factory=lambda: blob.BlobCredentials(
            token=settings.blob_read_write_token.get_secret_value(),
            store_id=settings.blob_store_id,
        )
    )
    try:
        with session(
            service_options=[options],
            httpx_client_factory=lambda: httpx2.Client(
                timeout=20, follow_redirects=False
            ),
        ):
            yield blob
    except blob.BlobNotFoundError:
        raise FileNotFoundError("Stored PDF is unavailable") from None
    except (blob.BlobError, httpx2.HTTPError):
        raise StorageUnavailable("Private document storage is unavailable") from None


def put(organization_id: str, key: str, content: bytes) -> None:
    name = object_name(organization_id, key)
    if settings.storage_backend == "local":
        path = settings.storage_dir.resolve() / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as file:
            file.write(content)
        return
    with cloud() as client:
        client.put_blob(
            name,
            content,
            access="private",
            content_type="application/pdf",
            add_random_suffix=False,
            allow_overwrite=False,
        )


def read(organization_id: str, key: str) -> bytes:
    name = object_name(organization_id, key)
    if settings.storage_backend == "local":
        return (settings.storage_dir.resolve() / name).read_bytes()
    # Bound response bytes too; no public URL or token reaches the browser.
    with cloud() as client, client.stream_blob(name, access="private") as download:
        content = bytearray()
        for chunk in download:
            content.extend(chunk)
            if len(content) > settings.file_limit("pdf"):
                raise StorageUnavailable("PDF exceeds the hosted download limit")
        return bytes(content)


def remove(organization_id: str, key: str) -> None:
    name = object_name(organization_id, key)
    if settings.storage_backend == "local":
        (settings.storage_dir.resolve() / name).unlink(missing_ok=True)
    else:
        with cloud() as client:
            client.delete_blob(name)
