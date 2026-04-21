#!/usr/bin/env python3
"""
Демо-данные для владельца и выгульщика.

1) Владелец (по умолчанию demo.owner@example.com): собаки из списка DOGS (по умолчанию две)
   и открытые бронирования в Санкт-Петербурге.

   Переменные (опционально):
   SEED_DOG_LIMIT=1 — не больше N собак из DOGS (по умолчанию все).
   SEED_OWNER_BOOKING_COUNT=10 — ровно столько заявок (районы по кругу);
   если не задано — по 3 заявки на каждую созданную собаку, как раньше.

2) Выгульщик (по умолчанию demo.walker@example.com): регистрация с role_key
   walker, профиль POST /walkers/me, отклики на первые N открытых заявок.

Режим монолита (по умолчанию):
  MONOLITH_BASE_URL или MONOLITH_URL (приоритет у MONOLITH_URL), например
  https://dogapp-02y1.onrender.com — один хост, пути /account/api/v1 и /booking/api/v1.

Режим микросервисов (если заданы оба URL):
  ACCOUNT_URL=http://127.0.0.1:8000
  BOOKING_URL=http://127.0.0.1:8001
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone


def _api_bases() -> tuple[str, str]:
    legacy_a = os.environ.get("ACCOUNT_URL", "").strip().rstrip("/")
    legacy_b = os.environ.get("BOOKING_URL", "").strip().rstrip("/")
    if legacy_a and legacy_b:
        return f"{legacy_a}/api/v1", f"{legacy_b}/api/v1"
    mono = (
        os.environ.get("MONOLITH_URL", "").strip().rstrip("/")
        or os.environ.get("MONOLITH_BASE_URL", "").strip().rstrip("/")
        or "http://127.0.0.1:9000"
    )
    return f"{mono}/account/api/v1", f"{mono}/booking/api/v1"


ACCOUNT_API, BOOKING_API = _api_bases()

OWNER_EMAIL = os.environ.get("SEED_OWNER_EMAIL", "demo.owner@example.com")
OWNER_PASSWORD = os.environ.get("SEED_OWNER_PASSWORD", "DemoOwner1")
OWNER_FIRST_NAME = os.environ.get("SEED_OWNER_FIRST_NAME", "Демо")
OWNER_LAST_NAME = os.environ.get("SEED_OWNER_LAST_NAME", "Владелец")
OWNER_CITY = os.environ.get("SEED_OWNER_CITY", "Санкт-Петербург")

WALKER_EMAIL = os.environ.get("SEED_WALKER_EMAIL", "demo.walker@example.com")
WALKER_PASSWORD = os.environ.get("SEED_WALKER_PASSWORD", "DemoWalker1")
WALKER_FIRST_NAME = os.environ.get("SEED_WALKER_FIRST_NAME", "Демо")
WALKER_LAST_NAME = os.environ.get("SEED_WALKER_LAST_NAME", "Выгульщик")
WALKER_CITY = os.environ.get("SEED_WALKER_CITY", "Санкт-Петербург")
WALKER_APPLY_MAX = int(os.environ.get("SEED_WALKER_APPLY_MAX", "8"))

_dog_limit_raw = os.environ.get("SEED_DOG_LIMIT", "").strip()
DOG_LIMIT = int(_dog_limit_raw) if _dog_limit_raw else len(DOGS)

_booking_count_raw = os.environ.get("SEED_OWNER_BOOKING_COUNT", "").strip()
OWNER_BOOKING_COUNT: int | None = int(_booking_count_raw) if _booking_count_raw else None

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


def _request(
    method: str,
    url: str,
    *,
    headers: dict | None = None,
    data: dict | None = None,
    expect_codes: tuple[int, ...] | None = None,
) -> tuple[int, dict | list]:
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
        if expect_codes and e.code in expect_codes:
            return e.code, detail
        print(f"HTTP {e.code} {url}: {detail}", file=sys.stderr)
        raise SystemExit(1) from None


def _login(email: str, password: str) -> str:
    code, payload = _request(
        "POST",
        f"{ACCOUNT_API}/auth/login",
        data={"email": email, "password": password},
    )
    if code != 200:
        print(payload, file=sys.stderr)
        raise SystemExit(1)
    return str(payload["access_token"])


def _ensure_owner_registered() -> None:
    code, _payload = _request(
        "POST",
        f"{ACCOUNT_API}/auth/register",
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
        expect_codes=(200, 201, 400, 409),
    )
    if code in (200, 201):
        print(f"Создан владелец: {OWNER_EMAIL}")


def _owner_token() -> str:
    try:
        return _login(OWNER_EMAIL, OWNER_PASSWORD)
    except SystemExit:
        _ensure_owner_registered()
        return _login(OWNER_EMAIL, OWNER_PASSWORD)


def _ensure_walker_registered() -> None:
    code, _payload = _request(
        "POST",
        f"{ACCOUNT_API}/auth/register",
        data={
            "email": WALKER_EMAIL,
            "first_name": WALKER_FIRST_NAME,
            "last_name": WALKER_LAST_NAME,
            "city": WALKER_CITY,
            "password": WALKER_PASSWORD,
            "consent_personal_data": True,
            "consent_privacy_policy": True,
            "role_key": "walker",
        },
        expect_codes=(200, 201, 400, 409),
    )
    if code in (200, 201):
        print(f"Создан выгульщик: {WALKER_EMAIL}")


def _walker_token() -> str:
    try:
        return _login(WALKER_EMAIL, WALKER_PASSWORD)
    except SystemExit:
        _ensure_walker_registered()
        return _login(WALKER_EMAIL, WALKER_PASSWORD)


def _create_dog(token: str, spec: dict) -> str:
    code, payload = _request(
        "POST",
        f"{BOOKING_API}/dogs/",
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


def _create_booking(
    token: str,
    dog_id: str,
    district: dict,
    scheduled_at: datetime,
    duration_minutes: int = 45,
) -> str:
    code, payload = _request(
        "POST",
        f"{BOOKING_API}/bookings/",
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


def _ensure_walker_profile(token: str) -> None:
    code, _p = _request(
        "POST",
        f"{BOOKING_API}/walkers/me",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "bio": "Демо-профиль для тестов приложения.",
            "experience_years": 2,
            "price_per_hour": "450.00",
            "latitude": 59.9342,
            "longitude": 30.3350,
            "service_radius_km": 25.0,
        },
        expect_codes=(201, 409),
    )
    if code == 201:
        print("Создан профиль выгульщика (walkers/me).")
    elif code == 409:
        print("Профиль выгульщика уже есть — пропуск создания.")


def _list_open_bookings(token: str) -> list[dict]:
    code, payload = _request(
        "GET",
        f"{BOOKING_API}/bookings/open",
        headers={"Authorization": f"Bearer {token}"},
    )
    if code != 200:
        print(payload, file=sys.stderr)
        raise SystemExit(1)
    assert isinstance(payload, list)
    return payload


def _apply_to_booking(walker_token: str, booking_id: str) -> bool:
    code, payload = _request(
        "POST",
        f"{BOOKING_API}/bookings/{booking_id}/applications/",
        headers={"Authorization": f"Bearer {walker_token}"},
        expect_codes=(200, 201, 400, 409),
    )
    if code in (200, 201):
        print(f"  Отклик на заявку {booking_id[:8]}…")
        return True
    detail = payload if isinstance(payload, dict) else {}
    d = detail.get("detail")
    print(f"  Пропуск {booking_id[:8]}… — {d}", file=sys.stderr)
    return False


def _seed_owner() -> None:
    now = datetime.now(timezone.utc)
    token = _owner_token()
    print("Владелец авторизован.")

    limit = max(1, min(DOG_LIMIT, len(DOGS)))
    dog_specs = DOGS[:limit]
    dog_ids: list[str] = []
    for spec in dog_specs:
        did = _create_dog(token, spec)
        dog_ids.append(did)
        print(f"Собака «{spec['name']}»: id={did}")

    if OWNER_BOOKING_COUNT is not None:
        n = max(1, OWNER_BOOKING_COUNT)
        for slot in range(n):
            dog_id = dog_ids[slot % len(dog_ids)]
            d = DISTRICTS[slot % len(DISTRICTS)]
            start = now + timedelta(days=1 + slot, hours=10 + (slot % 5) * 2)
            bid = _create_booking(token, dog_id, d, start)
            print(f"  Бронирование {bid[:8]}… — {d['label']} ({start.isoformat()})")
    else:
        slot = 0
        for i, dog_id in enumerate(dog_ids):
            for j in range(3):
                d = DISTRICTS[i * 3 + j]
                start = now + timedelta(days=1 + slot, hours=10 + j * 2)
                slot += 1
                bid = _create_booking(token, dog_id, d, start)
                print(f"  Бронирование {bid[:8]}… — {d['label']} ({start.isoformat()})")


def _seed_walker() -> None:
    token = _walker_token()
    print("Выгульщик авторизован.")
    _ensure_walker_profile(token)
    open_rows = _list_open_bookings(token)
    if not open_rows:
        print("Нет открытых заявок для откликов.")
        return
    print(f"Открытых заявок: {len(open_rows)}, откликаемся на до {WALKER_APPLY_MAX}.")
    applied = 0
    for row in open_rows:
        if applied >= WALKER_APPLY_MAX:
            break
        bid = str(row["id"])
        if _apply_to_booking(token, bid):
            applied += 1


def main() -> None:
    print(f"API: account={ACCOUNT_API} booking={BOOKING_API}")
    _seed_owner()
    _seed_walker()
    print("Готово.")


if __name__ == "__main__":
    main()
