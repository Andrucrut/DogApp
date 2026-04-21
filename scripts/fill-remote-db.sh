#!/usr/bin/env bash
# Схема + демо-данные для БД на Render (или любой удалённый Postgres + уже поднятый монолит).
#
# Создайте в корне репозитория файл render.secrets.env (в .gitignore), две строки:
#   MONOLITH_DATABASE_URL=postgresql://USER:PASS@....frankfurt-postgres.render.com/dogappdb_r7x8
#   MONOLITH_BASE_URL=https://dogapp-02y1.onrender.com
#
# Затем из корня DogApp:
#   bash scripts/fill-remote-db.sh
#
# Если init всё равно таймаутится до frankfurt-postgres: VPN / другая сеть
# или INIT_DB_RETRIES=10 INIT_DB_RETRY_SLEEP=40 bash scripts/fill-remote-db.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SECRETS="$ROOT/render.secrets.env"
if [[ -f "$SECRETS" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$SECRETS"
  set +a
fi

DB_URL="${MONOLITH_DATABASE_URL:-${DATABASE_URL:-}}"
if [[ -z "$DB_URL" ]]; then
  echo "Нет MONOLITH_DATABASE_URL / DATABASE_URL." >&2
  echo "Создайте $SECRETS (см. комментарии в начале scripts/fill-remote-db.sh)." >&2
  exit 1
fi

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  echo "Нужен python3 или .venv в корне DogApp." >&2
  exit 1
fi

export DATABASE_URL="$DB_URL"
export MONOLITH_DATABASE_URL="$DB_URL"

echo ">>> создание таблиц…"
if command -v psql >/dev/null 2>&1; then
  bash "$ROOT/scripts/init-monolith-via-psql.sh"
else
  PYTHONPATH=. "$PY" scripts/init-monolith-db.py
fi

BASE="${MONOLITH_URL:-${MONOLITH_BASE_URL:-}}"
if [[ -z "$BASE" ]]; then
  echo ">>> Сиды пропущены: нет MONOLITH_BASE_URL / MONOLITH_URL (добавьте в render.secrets.env)." >&2
  exit 0
fi

echo ">>> seed-via-api (демо через HTTP)…"
PYTHONPATH=. "$PY" scripts/seed-via-api.py --url "$BASE" --skip-health

echo "Готово."
