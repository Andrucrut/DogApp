#!/usr/bin/env bash
# Останавливает процессы, запущенные scripts/start-all.sh (PID-ы в .run/pids).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT/.run/pids"

if [[ ! -f "$PID_FILE" ]]; then
  echo "Файл $PID_FILE не найден — нечего останавливать (или сервисы не запускались этим скриптом)."
  exit 0
fi

while read -r pid; do
  [[ -z "$pid" ]] && continue
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
  fi
done <"$PID_FILE"

rm -f "$PID_FILE"
echo "Готово: отправлен сигнал завершения процессам из $PID_FILE"
