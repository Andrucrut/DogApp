#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os

from sqlalchemy.ext.asyncio import create_async_engine

from monolith_loader import _ensure_asyncpg_database_url, load_service_models


SERVICE_NAMES = [
    "account",
    "booking",
    "tracking",
    "media",
    "payment",
    "review",
    "notification",
]


async def main() -> None:
    database_url = os.getenv("MONOLITH_DATABASE_URL", "").strip() or os.getenv(
        "DATABASE_URL", ""
    ).strip()
    if not database_url:
        raise RuntimeError(
            "Set MONOLITH_DATABASE_URL or DATABASE_URL before running init-monolith-db.py"
        )
    database_url = _ensure_asyncpg_database_url(database_url)

    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            for service_name in SERVICE_NAMES:
                loaded = load_service_models(service_name)
                await conn.run_sync(loaded.base.metadata.create_all)
                print(f"[init-monolith-db] created metadata for {service_name}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
