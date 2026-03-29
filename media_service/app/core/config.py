from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    UPLOAD_DIR: Path = Path("./data/media_uploads")
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024

    class Config:
        env_file = ".env"


settings = Settings()
