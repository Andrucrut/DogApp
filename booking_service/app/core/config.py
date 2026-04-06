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
    ACCOUNT_SERVICE_SECRET_KEY: str | None = None
    ALGORITHM: str = "HS256"
    INTERNAL_API_TOKEN: str = "change-me-internal"
    ACCOUNT_SERVICE_URL: str | None = None
    NOTIFICATION_SERVICE_URL: str | None = None
    GEOCODER_PROVIDER: str = "nominatim"  # nominatim|yandex (optional)
    YANDEX_GEOCODER_API_KEY: str | None = None
    HTTP_TIMEOUT_SECONDS: float = 5.0


settings = Settings()
