from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import FastAPI

from monolith_loader import load_service_app


SERVICE_PREFIXES = {
    "account": "/account",
    "booking": "/booking",
    "tracking": "/tracking",
    "media": "/media",
    "payment": "/payment",
    "review": "/review",
    "notification": "/notification",
}

SERVICE_APPS = {
    service_name: load_service_app(service_name)
    for service_name in SERVICE_PREFIXES
}


async def _notification_due_worker() -> None:
    loaded = SERVICE_APPS["notification"]
    session_module = loaded.modules["app.db.session"]
    crud_notification_module = loaded.modules["app.db_crud.notification_crud"]
    crud_scheduled_module = loaded.modules["app.db_crud.scheduled_crud"]
    async_session_maker = getattr(session_module, "async_session_maker")
    crud_notification = getattr(crud_notification_module, "crud_notification")
    crud_scheduled = getattr(crud_scheduled_module, "crud_scheduled")
    datetime_cls = loaded.modules["app.main"].datetime
    timezone_cls = loaded.modules["app.main"].timezone

    while True:
        await asyncio.sleep(30)
        try:
            async with async_session_maker() as db:
                due = await crud_scheduled.list_due(db)
                for item in due:
                    await crud_notification.create(
                        db,
                        {
                            "user_id": item.user_id,
                            "title": item.title,
                            "body": item.body,
                            "data": item.data,
                            "channel": "in_app",
                        },
                    )
                    await crud_scheduled.update(
                        db,
                        item,
                        {"sent_at": datetime_cls.now(timezone_cls.utc)},
                    )
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_notification_due_worker())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="DogApp Monolith", lifespan=lifespan)

for service_name, prefix in SERVICE_PREFIXES.items():
    app.mount(prefix, SERVICE_APPS[service_name].fastapi_app)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "mode": "monolith",
        "services": list(SERVICE_PREFIXES.keys()),
    }


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
