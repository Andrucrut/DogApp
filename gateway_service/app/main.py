from typing import Any

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(title="API Gateway", description="HTTP proxy to microservices (WebSocket — напрямую в tracking).")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_SERVICE_MAP: dict[str, str] = {
    "account": settings.ACCOUNT_SERVICE_URL,
    "booking": settings.BOOKING_SERVICE_URL,
    "tracking": settings.TRACKING_SERVICE_URL,
    "media": settings.MEDIA_SERVICE_URL,
    "payment": settings.PAYMENT_SERVICE_URL,
    "review": settings.REVIEW_SERVICE_URL,
    "notification": settings.NOTIFICATION_SERVICE_URL,
}


def _filter_request_headers(headers: httpx.Headers) -> dict[str, str]:
    skip = {"host", "content-length", "connection"}
    return {k: v for k, v in headers.items() if k.lower() not in skip}


def _filter_response_headers(headers: httpx.Headers) -> dict[str, str]:
    skip = {"content-encoding", "transfer-encoding", "connection", "content-length"}
    return {k: v for k, v in headers.items() if k.lower() not in skip}


@app.api_route(
    "/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy(service: str, path: str, request: Request) -> Response:
    base = _SERVICE_MAP.get(service)
    if not base:
        return Response(status_code=404, content=b'{"detail":"unknown_service"}')
    url = f"{base.rstrip('/')}/api/v1/{path}"
    body = await request.body()
    req_headers = _filter_request_headers(request.headers)
    async with httpx.AsyncClient(follow_redirects=False) as client:
        upstream = await client.request(
            request.method,
            url,
            params=request.query_params,
            content=body if body else None,
            headers=req_headers,
            timeout=120.0,
        )
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=_filter_response_headers(upstream.headers),
        media_type=upstream.headers.get("content-type"),
    )


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "services": list(_SERVICE_MAP.keys())}
