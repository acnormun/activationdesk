"""Application settings (loaded from .env when present)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "dev-secret-key-change-me"
    database_url: str = "sqlite:///./activationdesk.dev.db"
    token_ttl_minutes: int = 480
    cookie_name: str = "activationdesk_session"
    algorithm: str = "HS256"
    # Comma-separated origins allowed to call the API with cookies (CORS).
    allowed_origins: str = "http://localhost:3000"


settings = Settings()


def parse_origins(raw: str) -> list[str]:
    """Split a comma-separated ALLOWED_ORIGINS value into clean origins."""
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
