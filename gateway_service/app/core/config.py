from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ACCOUNT_SERVICE_URL: str = "http://127.0.0.1:8000"
    BOOKING_SERVICE_URL: str = "http://127.0.0.1:8001"
    TRACKING_SERVICE_URL: str = "http://127.0.0.1:8002"
    MEDIA_SERVICE_URL: str = "http://127.0.0.1:8003"
    PAYMENT_SERVICE_URL: str = "http://127.0.0.1:8004"
    REVIEW_SERVICE_URL: str = "http://127.0.0.1:8005"
    NOTIFICATION_SERVICE_URL: str = "http://127.0.0.1:8006"

    class Config:
        env_file = ".env"


settings = Settings()
