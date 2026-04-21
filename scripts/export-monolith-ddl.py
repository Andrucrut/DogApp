#!/usr/bin/env python3
"""
DDL монолита (CREATE TYPE / TABLE / INDEX …). Без подключения к БД.

  В stdout целиком:
    PYTHONPATH=. python scripts/export-monolith-ddl.py > /tmp/dogapp_monolith.sql

  Каталог с шагами (один SQL = один файл — короткий psql, меньше таймаутов на Render):
    PYTHONPATH=. python scripts/export-monolith-ddl.py --out-dir /tmp/dogapp_ddl
    # появится /tmp/dogapp_ddl/steps/0001-account.sql, …
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import create_mock_engine

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


def _idempotent_ddl(statement: str) -> str:
    """Повторный прогон: типы/таблицы/индексы уже есть после обрыва или частичного init."""
    s = statement.strip().rstrip(";")
    if not s:
        return ""

    if re.match(r"^CREATE\s+TYPE\s+", s, re.I) and re.search(r"\sAS\s+ENUM\s*\(", s, re.I):
        return (
            "DO $iddl$ BEGIN\n"
            f"  {s};\n"
            "EXCEPTION WHEN duplicate_object THEN NULL;\n"
            "END $iddl$;"
        )

    if re.match(r"^CREATE\s+TABLE\s+", s, re.I) and not re.search(r"IF\s+NOT\s+EXISTS", s, re.I):
        s = re.sub(r"^CREATE\s+TABLE\s+", "CREATE TABLE IF NOT EXISTS ", s, count=1, flags=re.I)
        return s + ";"

    if re.match(r"^CREATE\s+UNIQUE\s+INDEX\s+", s, re.I) and not re.search(
        r"IF\s+NOT\s+EXISTS", s, re.I
    ):
        s = re.sub(
            r"^CREATE\s+UNIQUE\s+INDEX\s+",
            "CREATE UNIQUE INDEX IF NOT EXISTS ",
            s,
            count=1,
            flags=re.I,
        )
        return s + ";"

    if re.match(r"^CREATE\s+INDEX\s+", s, re.I) and not re.match(
        r"^CREATE\s+INDEX\s+CONCURRENTLY\s+", s, re.I
    ):
        if not re.search(r"IF\s+NOT\s+EXISTS", s, re.I):
            s = re.sub(r"^CREATE\s+INDEX\s+", "CREATE INDEX IF NOT EXISTS ", s, count=1, flags=re.I)
        return s + ";"

    return s + ";"


def _ddl_for_service(service_name: str) -> list[str]:
    dialect = postgresql.dialect()
    lines: list[str] = []

    def dump(sql, *args, **kwargs) -> None:
        stmt = str(sql.compile(dialect=dialect)).strip()
        if not stmt:
            return
        lines.append(_idempotent_ddl(stmt))

    engine = create_mock_engine("postgresql+psycopg://", dump)
    loaded = load_service_models(service_name)
    loaded.base.metadata.create_all(engine, checkfirst=False)
    return lines


def main() -> None:
    os.environ.setdefault("MONOLITH_DATABASE_URL", "postgresql://127.0.0.1:5432/placeholder")
    os.environ.setdefault("MONOLITH_SECRET_KEY", "01234567890123456789012345678901")
    os.environ.setdefault("MONOLITH_INTERNAL_API_TOKEN", "local-ddl-export-token")

    p = argparse.ArgumentParser(description="Экспорт DDL монолита DogApp.")
    p.add_argument(
        "--out-dir",
        type=Path,
        metavar="DIR",
        help="Писать DIR/steps/0001-account.sql, … (одна команда DDL на файл)",
    )
    args = p.parse_args()

    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        steps = args.out_dir / "steps"
        steps.mkdir(parents=True, exist_ok=True)
        n = 0
        for name in SERVICE_NAMES:
            for stmt in _ddl_for_service(name):
                n += 1
                path = steps / f"{n:04d}-{name}.sql"
                path.write_text(stmt + "\n", encoding="utf-8")
        print(f"wrote {n} files under {steps}", file=sys.stderr)
        return

    all_lines: list[str] = []
    for name in SERVICE_NAMES:
        all_lines.extend(_ddl_for_service(name))
    sys.stdout.write("\n".join(all_lines))
    if all_lines:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
