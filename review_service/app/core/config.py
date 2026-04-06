from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_SERVICE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_SERVICE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    BOOKING_SERVICE_URL: str = "http://127.0.0.1:8001"
    INTERNAL_API_TOKEN: str = "change-me-internal"
    HTTP_TIMEOUT_SECONDS: float = 10.0


settings = Settings()
