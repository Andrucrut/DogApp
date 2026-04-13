from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


ROOT_DIR = Path(__file__).resolve().parent


def _asyncpg_url_without_sslmode(url: str) -> str:
    """
    Render/DigitalOcean и др. кладут в DATABASE_URL ?sslmode=require.
    SQLAlchemy передаёт query в asyncpg.connect(), а asyncpg не принимает sslmode → 500 на первом запросе к БД.
    Убираем sslmode и при необходимости задаём ssl=require (облачный Postgres с TLS).
    """
    parsed = urlparse(url)
    if "asyncpg" not in parsed.scheme.lower():
        return url
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if str(q.get("ssl", "")).lower() in ("true", "1", "yes"):
        q["ssl"] = "require"
    sslmode = (q.pop("sslmode", None) or "").strip().lower()
    # Не «ssl=true» в строке: SQLAlchemy передаст asyncpg ssl='true', что даёт ClientConfigurationError.
    # Допустимые значения см. asyncpg; для облака достаточно require.
    if sslmode in ("require", "verify-full", "verify-ca", "prefer", "allow"):
        q.setdefault("ssl", "require")
    new_query = urlencode(list(q.items()))
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )


def _ensure_asyncpg_database_url(url: str) -> str:
    """postgres:// и postgresql:// без асинхронного драйвера → SQLAlchemy тянет psycopg2; async-код ждёт asyncpg."""
    u = url.strip()
    if not u or "://" not in u:
        return u
    scheme, rest = u.split("://", 1)
    s = scheme.lower()
    if "asyncpg" in s:
        return _asyncpg_url_without_sslmode(u)
    if s in {"postgres", "postgresql"}:
        return _asyncpg_url_without_sslmode(f"postgresql+asyncpg://{rest}")
    return u


SERVICE_DIRS: dict[str, Path] = {
    "account": ROOT_DIR / "account_service",
    "booking": ROOT_DIR / "booking_service",
    "tracking": ROOT_DIR / "tracking_service",
    "media": ROOT_DIR / "media_service",
    "payment": ROOT_DIR / "payment_service",
    "review": ROOT_DIR / "review_service",
    "notification": ROOT_DIR / "notification_service",
}

BASE_MODULES: dict[str, str] = {
    "account": "app.models.base",
    "booking": "app.models.base",
    "tracking": "app.models.base",
    "media": "app.models.base",
    "payment": "app.models.base",
    "review": "app.models.base",
    "notification": "app.models.base",
}


@dataclass
class LoadedService:
    name: str
    service_dir: Path
    fastapi_app: object
    modules: dict[str, ModuleType]


@dataclass
class LoadedModels:
    name: str
    service_dir: Path
    base: object
    modules: dict[str, ModuleType]


def _clear_service_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


def _snapshot_service_modules() -> dict[str, ModuleType]:
    return {
        module_name: module
        for module_name, module in sys.modules.items()
        if module_name == "app" or module_name.startswith("app.")
    }


def _restore_env(previous_env: dict[str, str | None]) -> None:
    for key, previous_value in previous_env.items():
        if previous_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous_value


def _service_env() -> dict[str, str]:
    base_url = os.getenv("MONOLITH_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
    database_url = os.getenv("MONOLITH_DATABASE_URL", "").strip()
    if not database_url:
        # Render часто подставляет только DATABASE_URL от linked PostgreSQL, без MONOLITH_*.
        database_url = os.getenv("DATABASE_URL", "").strip()
    secret_key = os.getenv(
        "MONOLITH_SECRET_KEY",
        os.getenv("SECRET_KEY", "change-me-monolith-secret"),
    )
    internal_api_token = os.getenv(
        "MONOLITH_INTERNAL_API_TOKEN",
        os.getenv("INTERNAL_API_TOKEN", "change-me-monolith-internal"),
    )

    env = {
        "SECRET_KEY": secret_key,
        "INTERNAL_API_TOKEN": internal_api_token,
        "ACCOUNT_SERVICE_URL": f"{base_url}/account",
        "BOOKING_SERVICE_URL": f"{base_url}/booking",
        "TRACKING_SERVICE_URL": f"{base_url}/tracking",
        "MEDIA_SERVICE_URL": f"{base_url}/media",
        "PAYMENT_SERVICE_URL": f"{base_url}/payment",
        "REVIEW_SERVICE_URL": f"{base_url}/review",
        "NOTIFICATION_SERVICE_URL": f"{base_url}/notification",
    }
    if database_url:
        env["DATABASE_URL"] = _ensure_asyncpg_database_url(database_url)
    return env


def _import_from_service_dir(
    service_dir: Path,
    import_callback,
):
    service_env = _service_env()
    previous_env = {key: os.environ.get(key) for key in service_env}
    _clear_service_modules()
    sys.path.insert(0, str(service_dir))
    try:
        for key, value in service_env.items():
            os.environ[key] = value
        result = import_callback()
        modules = _snapshot_service_modules()
        return result, modules
    finally:
        if sys.path and sys.path[0] == str(service_dir):
            sys.path.pop(0)
        _clear_service_modules()
        _restore_env(previous_env)


def load_service_app(service_name: str) -> LoadedService:
    service_dir = SERVICE_DIRS[service_name]

    def _callback():
        module = importlib.import_module("app.main")
        return getattr(module, "app")

    fastapi_app, modules = _import_from_service_dir(service_dir, _callback)
    return LoadedService(
        name=service_name,
        service_dir=service_dir,
        fastapi_app=fastapi_app,
        modules=modules,
    )


def load_service_models(service_name: str) -> LoadedModels:
    service_dir = SERVICE_DIRS[service_name]
    models_dir = service_dir / "app" / "models"
    model_modules = [
        f"app.models.{path.stem}"
        for path in sorted(models_dir.glob("*.py"))
        if path.stem not in {"__init__", "base"}
    ]
    base_module_name = BASE_MODULES[service_name]

    def _callback():
        base_module = importlib.import_module(base_module_name)
        for module_name in model_modules:
            importlib.import_module(module_name)
        return getattr(base_module, "Base")

    base, modules = _import_from_service_dir(service_dir, _callback)
    return LoadedModels(
        name=service_name,
        service_dir=service_dir,
        base=base,
        modules=modules,
    )

