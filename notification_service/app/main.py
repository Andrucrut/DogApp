import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone

from fastapi import FastAPI

from app.api.router import api_router
from app.db.session import async_session_maker
from app.db_crud.notification_crud import crud_notification
from app.db_crud.scheduled_crud import crud_scheduled


async def _due_worker() -> None:
    while True:
        await asyncio.sleep(30)
        try:
            async with async_session_maker() as db:
                due = await crud_scheduled.list_due(db)
                for s in due:
                    await crud_notification.create(
                        db,
                        {
                            "user_id": s.user_id,
                            "title": s.title,
                            "body": s.body,
                            "data": s.data,
                            "channel": "in_app",
                        },
                    )
                    await crud_scheduled.update(
                        db,
                        s,
                        {"sent_at": datetime.now(timezone.utc)},
                    )
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_due_worker())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="Notification Service", lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
