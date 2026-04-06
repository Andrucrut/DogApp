import logging
from uuid import UUID

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def fetch_public_profiles(user_ids: list[UUID]) -> dict[UUID, dict]:
    """Load first_name, last_name, avatar, city from account_service (batched)."""
    base = (settings.ACCOUNT_SERVICE_URL or "").strip().rstrip("/")
    if not base or not user_ids:
        return {}
    url = f"{base}/api/v1/internal/users/public-profiles"
    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                url,
                json={"user_ids": [str(x) for x in user_ids]},
                headers={"X-Internal-Token": settings.INTERNAL_API_TOKEN},
            )
        if resp.status_code != 200:
            logger.warning(
                "account public-profiles failed: %s %s",
                resp.status_code,
                resp.text[:200],
            )
            return {}
        data = resp.json()
        out: dict[UUID, dict] = {}
        for item in data.get("items", []):
            try:
                uid = UUID(item["id"])
            except (KeyError, ValueError):
                continue
            out[uid] = item
        return out
    except Exception:
        logger.exception("account public-profiles request error")
        return {}
