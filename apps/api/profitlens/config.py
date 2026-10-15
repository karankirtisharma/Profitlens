from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = (
        "postgresql+psycopg://profitlens:change-me@localhost:5432/profitlens"
    )
    web_origin: str = "http://localhost:3000"
    cookie_secure: bool = False
    storage_dir: Path = Path("data/uploads")
    session_hours: int = 8
    ai_provider: str = "disabled"
    ai_model: str = ""
    openrouter_api_key: SecretStr = SecretStr("")
    nvidia_api_key: SecretStr = SecretStr("")
    ai_timeout_seconds: int = 30


settings = Settings()
