from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    BOOKING_SERVICE_URL: str = "http://127.0.0.1:8001"
    INTERNAL_API_TOKEN: str = "change-me-internal"
    HTTP_TIMEOUT_SECONDS: float = 10.0

    class Config:
        env_file = ".env"


settings = Settings()
