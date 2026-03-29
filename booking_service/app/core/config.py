from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCOUNT_SERVICE_SECRET_KEY: str | None = None
    ALGORITHM: str = "HS256"
    INTERNAL_API_TOKEN: str = "change-me-internal"
    NOTIFICATION_SERVICE_URL: str | None = None
    GEOCODER_PROVIDER: str = "nominatim"  # nominatim|yandex (optional)
    YANDEX_GEOCODER_API_KEY: str | None = None
    HTTP_TIMEOUT_SECONDS: float = 5.0

    class Config:
        env_file = ".env"


settings = Settings()
