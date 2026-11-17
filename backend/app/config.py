"""Application settings (loaded from .env when present)."""

from pydantic import field_validator
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
    # Cookie flags: set SameSite=None + Secure=True on hosts where the API and
    # the frontend live on different origins (cross-domain deploys, e.g. Railway).
    cookie_samesite: str = "lax"
    cookie_secure: bool = False

    @field_validator("database_url")
    @classmethod
    def use_psycopg3_driver(cls, value: str) -> str:
        """Rewrite bare postgresql:// URLs to the installed psycopg 3 driver.

        Providers like Railway hand out postgresql:// URLs; SQLAlchemy would
        then pick psycopg2, which is not in requirements.txt.
        """
        if value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value[len("postgresql://"):]
        return value


settings = Settings()


def parse_origins(raw: str) -> list[str]:
    """Split a comma-separated ALLOWED_ORIGINS value into clean origins."""
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
