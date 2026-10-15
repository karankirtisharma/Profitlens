from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", hide_input_in_errors=True
    )
    app_env: Literal["development", "production"] = "development"
    vercel: bool = False
    database_url: str = (
        "postgresql+psycopg://profitlens:change-me@localhost:5432/profitlens"
    )
    web_origin: str = "http://localhost:3000"
    cookie_secure: bool = False
    storage_dir: Path = Path("data/uploads")
    storage_backend: Literal["local", "vercel_blob"] = "local"
    blob_read_write_token: SecretStr = SecretStr("")
    blob_store_id: str = ""
    database_pool_mode: Literal["queue", "null"] = "queue"
    upload_limit_bytes: int | None = Field(default=None, ge=1, le=10 * 1024 * 1024)
    session_hours: int = 8
    ai_provider: str = "disabled"
    ai_model: str = ""
    openrouter_api_key: SecretStr = SecretStr("")
    nvidia_api_key: SecretStr = SecretStr("")
    ai_timeout_seconds: int = 30

    @field_validator("database_url", mode="before")
    @classmethod
    def select_psycopg_driver(cls, value):
        """Accept provider-managed PostgreSQL URLs without altering credentials/TLS."""
        if isinstance(value, str):
            for prefix in ("postgresql://", "postgres://"):
                if value.startswith(prefix):
                    return "postgresql+psycopg://" + value[len(prefix) :]
        return value

    @model_validator(mode="after")
    def validate_hosted_settings(self):
        origin = urlsplit(self.web_origin)
        if (
            origin.path
            or origin.query
            or origin.fragment
            or origin.username
            or not origin.hostname
        ):
            raise ValueError(
                "WEB_ORIGIN must be an origin without a path or credentials"
            )
        if self.app_env == "production" or self.vercel:
            if origin.scheme != "https" or not self.cookie_secure:
                raise ValueError(
                    "Production requires HTTPS WEB_ORIGIN and COOKIE_SECURE=true"
                )
            url = make_url(self.database_url)
            if url.drivername != "postgresql+psycopg" or url.query.get(
                "sslmode"
            ) not in {"require", "verify-ca", "verify-full"}:
                raise ValueError(
                    "Production requires postgresql+psycopg and TLS sslmode"
                )
        if self.vercel:
            if self.storage_backend != "vercel_blob":
                raise ValueError(
                    "Vercel requires STORAGE_BACKEND=vercel_blob; local files are ephemeral"
                )
            if self.database_pool_mode != "null":
                raise ValueError("Vercel requires DATABASE_POOL_MODE=null")
            if self.upload_limit_bytes is None or self.upload_limit_bytes > 4_000_000:
                raise ValueError("Vercel requires UPLOAD_LIMIT_BYTES at most 4000000")
            if not 1 <= self.ai_timeout_seconds <= 20:
                raise ValueError("Vercel requires AI_TIMEOUT_SECONDS between 1 and 20")
        if self.storage_backend == "vercel_blob" and (
            not self.blob_read_write_token.get_secret_value() or not self.blob_store_id
        ):
            raise ValueError(
                "Private Blob requires BLOB_READ_WRITE_TOKEN and BLOB_STORE_ID"
            )
        return self

    def file_limit(self, kind: str) -> int:
        default = (5 if kind == "csv" else 10) * 1024 * 1024
        return min(default, self.upload_limit_bytes or default)

    @property
    def request_limit(self) -> int:
        return (
            self.upload_limit_bytes + 100_000
            if self.upload_limit_bytes
            else 11 * 1024 * 1024
        )


settings = Settings()
