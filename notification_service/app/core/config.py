from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    INTERNAL_API_TOKEN: str = "change-me-internal"

    class Config:
        env_file = ".env"


settings = Settings()
