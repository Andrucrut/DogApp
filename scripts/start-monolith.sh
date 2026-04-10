#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -f "$ROOT/monolith.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/monolith.env"
  set +a
fi

if [[ -z "${MONOLITH_DATABASE_URL:-}" ]]; then
  echo "Set MONOLITH_DATABASE_URL in monolith.env or environment." >&2
  exit 1
fi

cd "$ROOT"
exec ./.venv/bin/uvicorn main:app --host 0.0.0.0 --port 9000 --reload
