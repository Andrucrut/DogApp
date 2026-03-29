from __future__ import annotations

from urllib.parse import urlencode

import httpx

from app.core.config import settings


async def suggest_address(
    *,
    country: str,
    city: str,
    query: str,
    limit: int = 7,
) -> list[dict]:
    provider = (settings.GEOCODER_PROVIDER or "nominatim").lower()
    if provider == "yandex":
        return await _suggest_yandex(country=country, city=city, query=query, limit=limit)
    return await _suggest_nominatim(country=country, city=city, query=query, limit=limit)


async def _suggest_nominatim(*, country: str, city: str, query: str, limit: int) -> list[dict]:
    q = ", ".join([p for p in [query, city, country] if p])
    params = {
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": str(max(1, min(limit, 15))),
        "q": q,
    }
    url = f"https://nominatim.openstreetmap.org/search?{urlencode(params)}"
    headers = {"User-Agent": "DogApp/1.0 (booking_service)"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, timeout=settings.HTTP_TIMEOUT_SECONDS)
    if resp.status_code != 200:
        return []
    out: list[dict] = []
    for item in resp.json():
        addr = item.get("address") or {}
        out.append(
            {
                "label": item.get("display_name"),
                "country": addr.get("country"),
                "city": addr.get("city") or addr.get("town") or addr.get("village"),
                "street": addr.get("road") or addr.get("pedestrian") or addr.get("footway"),
                "house": addr.get("house_number"),
                "latitude": float(item["lat"]) if item.get("lat") else None,
                "longitude": float(item["lon"]) if item.get("lon") else None,
            }
        )
    return out


async def _suggest_yandex(*, country: str, city: str, query: str, limit: int) -> list[dict]:
    if not settings.YANDEX_GEOCODER_API_KEY:
        return []
    geocode = ", ".join([p for p in [country, city, query] if p])
    params = {
        "apikey": settings.YANDEX_GEOCODER_API_KEY,
        "format": "json",
        "geocode": geocode,
        "results": str(max(1, min(limit, 10))),
    }
    url = f"https://geocode-maps.yandex.ru/1.x/?{urlencode(params)}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=settings.HTTP_TIMEOUT_SECONDS)
    if resp.status_code != 200:
        return []
    data = resp.json()
    feats = (
        data.get("response", {})
        .get("GeoObjectCollection", {})
        .get("featureMember", [])
    )
    out: list[dict] = []
    for fm in feats:
        geo = (fm or {}).get("GeoObject") or {}
        meta = (geo.get("metaDataProperty") or {}).get("GeocoderMetaData") or {}
        text = meta.get("text")
        pos = (geo.get("Point") or {}).get("pos")  # "lon lat"
        lon = lat = None
        if isinstance(pos, str) and " " in pos:
            lon_s, lat_s = pos.split(" ", 1)
            try:
                lon = float(lon_s)
                lat = float(lat_s)
            except ValueError:
                lon = lat = None
        out.append(
            {
                "label": text,
                "country": country,
                "city": city,
                "street": query,
                "house": None,
                "latitude": lat,
                "longitude": lon,
            }
        )
    return out

