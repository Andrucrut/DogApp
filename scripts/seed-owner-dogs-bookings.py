#!/usr/bin/env python3
"""
Создаёт для демо-владельца (demo.owner@example.com) двух собак и по 3 открытых
бронирования (заявки на выгул) на каждую — в разных районах Санкт-Петербурга.

Требования: подняты account_service (8000) и booking_service (8001).
Переменные окружения: ACCOUNT_URL, BOOKING_URL (опционально).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone


ACCOUNT_URL = os.environ.get("ACCOUNT_URL", "http://127.0.0.1:8000").rstrip("/")
BOOKING_URL = os.environ.get("BOOKING_URL", "http://127.0.0.1:8001").rstrip("/")

OWNER_EMAIL = "demo.owner@example.com"
OWNER_PASSWORD = "DemoOwner1"

# Районы СПб: улица + координаты внутри bbox booking_service (geo.py)
DISTRICTS = [
    {
        "label": "Центральный / Невский",
        "street": "Невский проспект",
        "house": "28",
        "lat": 59.9342,
        "lon": 30.3350,
    },
    {
        "label": "Васильевский остров",
        "street": "Средний проспект В.О.",
        "house": "15",
        "lat": 59.9420,
        "lon": 30.2570,
    },
    {
        "label": "Петроградская сторона",
        "street": "Каменноостровский проспект",
        "house": "26",
        "lat": 59.9660,
        "lon": 30.3120,
    },
    {
        "label": "Выборгский район",
        "street": "проспект Энгельса",
        "house": "120",
        "lat": 60.0400,
        "lon": 30.3300,
    },
    {
        "label": "Московский район",
        "street": "Московский проспект",
        "house": "150",
        "lat": 59.8520,
        "lon": 30.3180,
    },
    {
        "label": "Приморский район",
        "street": "Комендантский проспект",
        "house": "51",
        "lat": 60.0080,
        "lon": 30.2580,
    },
]

DOGS = [
    {"name": "Барсик", "breed": "Джек-рассел-терьер", "weight_kg": 7.5, "gender": "male"},
    {"name": "Мурка", "breed": "Бордер-колли", "weight_kg": 18.0, "gender": "female"},
]


def _request(method: str, url: str, *, headers: dict | None = None, data: dict | None = None) -> tuple[int, dict | list]:
    body = None
    h = dict(headers or {})
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            code = resp.status
            if not raw:
                return code, {}
            return code, json.loads(raw)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        try:
            detail = json.loads(err_body)
        except json.JSONDecodeError:
            detail = {"raw": err_body}
        print(f"HTTP {e.code} {url}: {detail}", file=sys.stderr)
        raise SystemExit(1) from None


def login() -> str:
    code, payload = _request(
        "POST",
        f"{ACCOUNT_URL}/api/v1/auth/login",
        data={"email": OWNER_EMAIL, "password": OWNER_PASSWORD},
    )
    if code != 200:
        print(payload, file=sys.stderr)
        raise SystemExit(1)
    return str(payload["access_token"])


def create_dog(token: str, spec: dict) -> str:
    code, payload = _request(
        "POST",
        f"{BOOKING_URL}/api/v1/dogs/",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "name": spec["name"],
            "breed": spec["breed"],
            "weight_kg": spec["weight_kg"],
            "gender": spec["gender"],
            "is_vaccinated": True,
            "is_sterilized": False,
            "is_aggressive": False,
        },
    )
    if code != 201:
        print(payload, file=sys.stderr)
        raise SystemExit(1)
    return str(payload["id"])


def create_booking(
    token: str,
    dog_id: str,
    district: dict,
    scheduled_at: datetime,
    duration_minutes: int = 45,
) -> str:
    code, payload = _request(
        "POST",
        f"{BOOKING_URL}/api/v1/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "dog_id": dog_id,
            "scheduled_at": scheduled_at.isoformat().replace("+00:00", "Z"),
            "duration_minutes": duration_minutes,
            "address_country": "Россия",
            "address_city": "Санкт-Петербург",
            "address_street": district["street"],
            "address_house": district["house"],
            "meeting_latitude": district["lat"],
            "meeting_longitude": district["lon"],
            "owner_notes": f"Демо-заявка: {district['label']}",
        },
    )
    if code != 201:
        print(payload, file=sys.stderr)
        raise SystemExit(1)
    return str(payload["id"])


def main() -> None:
    now = datetime.now(timezone.utc)
    token = login()
    print("Владелец авторизован.")

    dog_ids: list[str] = []
    for spec in DOGS:
        did = create_dog(token, spec)
        dog_ids.append(did)
        print(f"Собака «{spec['name']}»: id={did}")

    # Первой собаке — районы 0..2, второй — 3..5; время в будущем, не пересекается
    slot = 0
    for i, dog_id in enumerate(dog_ids):
        for j in range(3):
            d = DISTRICTS[i * 3 + j]
            start = now + timedelta(days=1 + slot, hours=10 + j * 2)
            slot += 1
            bid = create_booking(token, dog_id, d, start)
            print(f"  Бронирование {bid[:8]}… — {d['label']} ({start.isoformat()})")

    print("Готово.")


if __name__ == "__main__":
    main()
