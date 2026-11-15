from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Secrets come from .env, never from source."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="HS_", extra="ignore")

    secret_key: str = "dev-only-insecure-secret-change-me"
    token_expire_minutes: int = 720
    database_url: str = "sqlite:///./healthsignal.sqlite3"
    allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_upload_mb: int = 10
    model_dir: str = "../ml/artifacts"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()