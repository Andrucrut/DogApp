from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.session import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(
            "База данных недоступна.\n"
            "1) Из корня DogApp: docker compose -f infra/docker-compose.yml up -d\n"
            "2) В account_service/.env: DATABASE_URL с портом 55432, например "
            "postgresql+asyncpg://dogapp:dogapp@localhost:55432/account_db\n"
            "3) Миграции: cd account_service && alembic upgrade head\n"
            f"Ошибка: {type(e).__name__}: {e}"
        ) from e
    yield


app = FastAPI(title="Account Service", lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}