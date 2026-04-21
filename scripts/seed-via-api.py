#!/usr/bin/env python3
"""
Наполнение БД через публичное HTTP API монолита (без строки подключения к Postgres).

Примеры:

  PYTHONPATH=. python scripts/seed-via-api.py --url https://dogapp-xxx.onrender.com

  export MONOLITH_BASE_URL=https://dogapp-xxx.onrender.com
  PYTHONPATH=. python scripts/seed-via-api.py

По умолчанию: владелец + выгульщик + заявки + отклики (scripts/seed-owner-dogs-bookings.py).
  Для «1 собака, 10 заявок в СПб»: SEED_DOG_LIMIT=1 SEED_OWNER_BOOKING_COUNT=10 SEED_WALKER_APPLY_MAX=10
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _resolve_base_url(url: str | None) -> str:
    if url and url.strip():
        return url.strip().rstrip("/")
    for key in ("MONOLITH_URL", "MONOLITH_BASE_URL"):
        v = os.environ.get(key, "").strip().rstrip("/")
        if v:
            return v
    raise SystemExit(
        "Задайте URL монолита:\n"
        "  python scripts/seed-via-api.py --url https://….onrender.com\n"
        "или переменную MONOLITH_BASE_URL / MONOLITH_URL в окружении."
    )


def _health_ok(base: str) -> bool:
    try:
        req = urllib.request.Request(f"{base}/health", method="GET")
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _run_script(env: dict[str, str], name: str) -> None:
    path = ROOT / "scripts" / name
    r = subprocess.run([sys.executable, str(path)], cwd=str(ROOT), env=env)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main() -> None:
    p = argparse.ArgumentParser(description="Демо-данные через API монолита DogApp.")
    p.add_argument(
        "--url",
        "-u",
        metavar="BASE",
        help="Базовый URL без слэша в конце (иначе MONOLITH_BASE_URL / MONOLITH_URL)",
    )
    p.add_argument(
        "--skip-health",
        action="store_true",
        help="Не вызывать GET /health перед сидом",
    )
    p.add_argument(
        "--owner-only",
        action="store_true",
        help="Только владелец: собаки и заявки (seed-monolith-owner-data.py), без выгульщика",
    )
    p.add_argument(
        "--owner-rich",
        action="store_true",
        help="После основного сида — доп. собаки и заявки (seed-monolith-owner-data.py)",
    )
    args = p.parse_args()

    if args.owner_only and args.owner_rich:
        p.error("Нельзя одновременно --owner-only и --owner-rich")

    base = _resolve_base_url(args.url)
    env = os.environ.copy()
    env["MONOLITH_BASE_URL"] = base

    pp = str(ROOT)
    if env.get("PYTHONPATH"):
        env["PYTHONPATH"] = pp + os.pathsep + env["PYTHONPATH"]
    else:
        env["PYTHONPATH"] = pp

    if not args.skip_health and not _health_ok(base):
        raise SystemExit(
            f"Не удалось получить {base}/health — проверьте URL и деплой "
            "(или повторите с --skip-health)."
        )

    if args.owner_only:
        _run_script(env, "seed-monolith-owner-data.py")
        print("Готово: только набор владельца (monolith owner).")
        return

    _run_script(env, "seed-owner-dogs-bookings.py")
    if args.owner_rich:
        print("--- Дополнительный набор владельца ---")
        _run_script(env, "seed-monolith-owner-data.py")
    print("Готово.")


if __name__ == "__main__":
    main()
