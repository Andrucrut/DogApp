#!/usr/bin/env python3
"""
Создание всех таблиц монолита в одной БД.

Sync + psycopg (libpq). Для Render с «падающим» маршрутом: hostaddr=IPv4,
keepalive в строке подключения, NullPool, повторы при OperationalError.
"""
from __future__ import annotations

import os
import socket
import time
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool

from monolith_loader import load_service_models


SERVICE_NAMES = [
    "account",
    "booking",
    "tracking",
    "media",
    "payment",
    "review",
    "notification",
]


def _sync_psycopg_url(raw: str) -> str:
    u = raw.strip()
    if u.startswith("postgres://"):
        u = "postgresql://" + u[len("postgres://") :]
    if u.startswith("postgresql+asyncpg://"):
        u = "postgresql://" + u[len("postgresql+asyncpg://") :]
    if u.startswith("postgresql://"):
        u = "postgresql+psycopg://" + u[len("postgresql://") :]
    if "render.com" in u and "sslmode" not in u.lower():
        u += ("&" if "?" in u else "?") + "sslmode=require"
    return u


def _render_connection_hardening(url: str) -> str:
    """IPv4 hostaddr + TCP keepalive — часто помогает при таймаутах до EU Render."""
    if "render.com" not in url.lower():
        return url
    p = urlparse(url)
    host = p.hostname
    if not host:
        return url
    q = dict(parse_qsl(p.query, keep_blank_values=True))
    if "hostaddr" not in q:
        try:
            infos = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
            if infos:
                q["hostaddr"] = infos[0][4][0]
        except OSError:
            pass
    q.setdefault("keepalives", "1")
    q.setdefault("keepalives_idle", "30")
    q.setdefault("keepalives_interval", "10")
    q.setdefault("keepalives_count", "5")
    return urlunparse(
        (p.scheme, p.netloc, p.path, p.params, urlencode(list(q.items())), p.fragment)
    )


def _run_once(sync_url: str) -> None:
    engine = create_engine(
        sync_url,
        poolclass=NullPool,
        connect_args={
            "connect_timeout": int(os.environ.get("INIT_DB_CONNECT_TIMEOUT", "180")),
            "prepare_threshold": None,
        },
    )
    try:
        with engine.begin() as conn:
            for service_name in SERVICE_NAMES:
                loaded = load_service_models(service_name)
                loaded.base.metadata.create_all(conn)
                print(f"[init-monolith-db] created metadata for {service_name}")
    finally:
        engine.dispose()


def main() -> None:
    database_url = os.getenv("MONOLITH_DATABASE_URL", "").strip() or os.getenv(
        "DATABASE_URL", ""
    ).strip()
    if not database_url:
        raise RuntimeError(
            "Set MONOLITH_DATABASE_URL or DATABASE_URL before running init-monolith-db.py"
        )
    sync_url = _render_connection_hardening(_sync_psycopg_url(database_url))

    attempts = int(os.environ.get("INIT_DB_RETRIES", "6"))
    last: Exception | None = None
    for i in range(attempts):
        try:
            _run_once(sync_url)
            return
        except (OperationalError, OSError) as e:
            last = e
            print(
                f"[init-monolith-db] попытка {i + 1}/{attempts} не удалась: {e!r}",
                flush=True,
            )
            if i + 1 < attempts:
                time.sleep(float(os.environ.get("INIT_DB_RETRY_SLEEP", "25")))
    assert last is not None
    raise last


if __name__ == "__main__":
    main()
