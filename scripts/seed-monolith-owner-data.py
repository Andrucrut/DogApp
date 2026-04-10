#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone


BASE_URL = os.environ.get("MONOLITH_URL", "http://127.0.0.1:9000").rstrip("/")
ACCOUNT_URL = f"{BASE_URL}/account/api/v1"
BOOKING_URL = f"{BASE_URL}/booking/api/v1"

OWNER_EMAIL = os.environ.get("SEED_OWNER_EMAIL", "demo.owner@example.com")
OWNER_PASSWORD = os.environ.get("SEED_OWNER_PASSWORD", "DemoOwner1")
OWNER_FIRST_NAME = os.environ.get("SEED_OWNER_FIRST_NAME", "Демо")
OWNER_LAST_NAME = os.environ.get("SEED_OWNER_LAST_NAME", "Владелец")
OWNER_CITY = os.environ.get("SEED_OWNER_CITY", "Санкт-Петербург")

DOGS = [
    {
        "name": "Арчи",
        "breed": "Корги",
        "birth_date": str(date(2021, 5, 14)),
        "weight_kg": 11.8,
        "gender": "male",
        "is_vaccinated": True,
        "is_sterilized": False,
        "is_aggressive": False,
        "medical_notes": "Аллергия на курицу, корм гипоаллергенный.",
        "behavior_notes": "Любит людей, тянет поводок первые 10 минут.",
    },
    {
        "name": "Луна",
        "breed": "Самоед",
        "birth_date": str(date(2020, 11, 3)),
        "weight_kg": 21.4,
        "gender": "female",
        "is_vaccinated": True,
        "is_sterilized": True,
        "is_aggressive": False,
        "medical_notes": "Без особенностей.",
        "behavior_notes": "Очень активная, любит бегать и играть с мячом.",
    },
    {
        "name": "Ричи",
        "breed": "Мопс",
        "birth_date": str(date(2019, 8, 22)),
        "weight_kg": 8.9,
        "gender": "male",
        "is_vaccinated": True,
        "is_sterilized": True,
        "is_aggressive": False,
        "medical_notes": "Нельзя долгие активные нагрузки в жару.",
        "behavior_notes": "Спокойный, любит короткие прогулки и воду с собой.",
    },
]

DISTRICTS = [
    {
        "label": "Центральный / Невский",
        "street": "Невский проспект",
        "house": "28",
        "apartment": "14",
        "lat": 59.9342,
        "lon": 30.3350,
    },
    {
        "label": "Васильевский остров",
        "street": "Средний проспект В.О.",
        "house": "15",
        "apartment": "23",
        "lat": 59.9420,
        "lon": 30.2570,
    },
    {
        "label": "Петроградская сторона",
        "street": "Каменноостровский проспект",
        "house": "26",
        "apartment": "7",
        "lat": 59.9660,
        "lon": 30.3120,
    },
    {
        "label": "Выборгский район",
        "street": "проспект Энгельса",
        "house": "120",
        "apartment": "64",
        "lat": 60.0400,
        "lon": 30.3300,
    },
    {
        "label": "Московский район",
        "street": "Московский проспект",
        "house": "150",
        "apartment": "11",
        "lat": 59.8520,
        "lon": 30.3180,
    },
    {
        "label": "Приморский район",
        "street": "Комендантский проспект",
        "house": "51",
        "apartment": "90",
        "lat": 60.0080,
        "lon": 30.2580,
    },
]


def request(
    method: str,
    url: str,
    *,
    headers: dict | None = None,
    data: dict | None = None,
) -> tuple[int, dict | list]:
    body = None
    final_headers = dict(headers or {})
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        final_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, headers=final_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            code = resp.status
            if not raw:
                return code, {}
            return code, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw}
        print(f"HTTP {exc.code} {url}: {payload}", file=sys.stderr)
        raise SystemExit(1) from None


def login() -> str:
    code, payload = request(
        "POST",
        f"{ACCOUNT_URL}/auth/login",
        data={"email": OWNER_EMAIL, "password": OWNER_PASSWORD},
    )
    if code != 200:
        print(payload, file=sys.stderr)
        raise SystemExit(1)
    return str(payload["access_token"])


def ensure_owner_exists() -> None:
    code, _payload = request(
        "POST",
        f"{ACCOUNT_URL}/auth/register",
        data={
            "email": OWNER_EMAIL,
            "first_name": OWNER_FIRST_NAME,
            "last_name": OWNER_LAST_NAME,
            "city": OWNER_CITY,
            "password": OWNER_PASSWORD,
            "consent_personal_data": True,
            "consent_privacy_policy": True,
            "role_key": "owner",
        },
    )
    if code in (200, 201):
        print(f"Created owner user: {OWNER_EMAIL}")


def create_dog(token: str, spec: dict) -> str:
    code, payload = request(
        "POST",
        f"{BOOKING_URL}/dogs/",
        headers={"Authorization": f"Bearer {token}"},
        data=spec,
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
    duration_minutes: int,
    note: str,
) -> str:
    code, payload = request(
        "POST",
        f"{BOOKING_URL}/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "dog_id": dog_id,
            "scheduled_at": scheduled_at.isoformat().replace("+00:00", "Z"),
            "duration_minutes": duration_minutes,
            "address_country": "Россия",
            "address_city": "Санкт-Петербург",
            "address_street": district["street"],
            "address_house": district["house"],
            "address_apartment": district["apartment"],
            "meeting_latitude": district["lat"],
            "meeting_longitude": district["lon"],
            "owner_notes": note,
        },
    )
    if code != 201:
        print(payload, file=sys.stderr)
        raise SystemExit(1)
    return str(payload["id"])


def main() -> None:
    try:
        token = login()
    except SystemExit:
        ensure_owner_exists()
        token = login()
    print(f"Owner login ok: {OWNER_EMAIL}")

    dog_ids: list[str] = []
    for dog in DOGS:
        dog_id = create_dog(token, dog)
        dog_ids.append(dog_id)
        print(f"Created dog {dog['name']}: {dog_id}")

    now = datetime.now(timezone.utc)
    durations = [30, 45, 60, 90, 40, 75]
    for idx, district in enumerate(DISTRICTS):
        dog_id = dog_ids[idx % len(dog_ids)]
        start = now + timedelta(days=idx + 1, hours=9 + (idx % 3) * 2)
        booking_id = create_booking(
            token,
            dog_id,
            district,
            start,
            durations[idx],
            f"Тестовая заявка для наполнения данных: {district['label']}.",
        )
        print(f"Created booking {booking_id[:8]}... for {district['label']}")

    print("Seeding complete.")


if __name__ == "__main__":
    main()
