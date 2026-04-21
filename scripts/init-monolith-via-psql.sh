#!/usr/bin/env bash
# Схема монолита: DDL по одному файлу на команду → отдельный psql на каждый шаг (минимум таймаутов на Render).
#
#   source render.secrets.env
#   bash scripts/init-monolith-via-psql.sh
#
# URL — реальный postgresql://… как в рабочем у вас psql (не USER:PASS и не … с многоточием).

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

# Сначала PSQLURL из render.secrets.env (тот же вид, что для ручного psql), иначе MONOLITH_DATABASE_URL / DATABASE_URL
RAW="${PSQLURL:-${MONOLITH_DATABASE_URL:-${DATABASE_URL:-}}}"
if [[ -z "$RAW" ]]; then
  echo "Задайте PSQLURL или MONOLITH_DATABASE_URL в render.secrets.env (или в окружении)." >&2
  exit 1
fi

PSQLURL="${RAW//+asyncpg/}"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
else
  PY=python3
fi

DDLDIR="${TMPDIR:-/tmp}/dogapp_monolith_ddl_$$"
mkdir -p "$DDLDIR"
echo ">>> DDL в каталог: $DDLDIR"
PYTHONPATH=. "$PY" scripts/export-monolith-ddl.py --out-dir "$DDLDIR"

STEPS="$DDLDIR/steps"
if [[ ! -d "$STEPS" ]]; then
  echo "Нет каталога $STEPS после export-monolith-ddl.py" >&2
  exit 1
fi

echo ">>> по одному шагу в psql (до 8 повторов на шаг)…"
while IFS= read -r f; do
  [[ -n "$f" ]] || continue
  echo "    $f"
  ok=0
  for attempt in 1 2 3 4 5 6 7 8; do
    if psql "$PSQLURL" -v ON_ERROR_STOP=1 -f "$f"; then
      ok=1
      break
    fi
    echo "    попытка $attempt не удалась, пауза 20с…" >&2
    sleep 20
  done
  if [[ "$ok" -ne 1 ]]; then
    echo "Не вышло применить $f — оставлены файлы в $DDLDIR" >&2
    exit 1
  fi
  sleep 1
done < <(find "$STEPS" -maxdepth 1 -name '*.sql' | sort)

echo ">>> Схема применена. (Каталог можно удалить: rm -rf $DDLDIR)"
