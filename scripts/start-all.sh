#!/usr/bin/env bash
# Полный локальный запуск DogApp: Postgres (Docker), миграции, все микросервисы и gateway.
#
# Использование:
#   ./scripts/start-all.sh              # всё подряд
#   ./scripts/start-all.sh --no-migrate # только Postgres + uvicorn
#   ./scripts/start-all.sh --migrate-only
#   ./scripts/start-all.sh --force      # сначала stop-all, затем запуск
#
# Требования: Docker, Python 3.11+ (для venv), в каждом сервисе файл .env (из env.sample).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$ROOT/.run"
LOG_DIR="$RUN_DIR/logs"
PID_FILE="$RUN_DIR/pids"

DO_MIGRATE=true
MIGRATE_ONLY=false
FORCE=false

for arg in "$@"; do
  case "$arg" in
    --no-migrate) DO_MIGRATE=false ;;
    --migrate-only) MIGRATE_ONLY=true ;;
    --force) FORCE=true ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *)
      echo "Неизвестный аргумент: $arg" >&2
      exit 1
      ;;
  esac
done

log() { echo "[start-all] $*"; }

require_file() {
  if [[ ! -f "$1" ]]; then
    log "Ошибка: нет файла $1"
    exit 1
  fi
}

pick_python() {
  if command -v python3.11 >/dev/null 2>&1; then
    echo "python3.11"
  elif command -v python3.12 >/dev/null 2>&1; then
    echo "python3.12"
  elif command -v python3 >/dev/null 2>&1; then
    echo "python3"
  else
    log "Нужен Python 3.11+ (python3.11 или python3)."
    exit 1
  fi
}

ensure_venv() {
  local py
  py="$(pick_python)"
  if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
    log "Создаю .venv ($py)…"
    (cd "$ROOT" && "$py" -m venv .venv)
  fi
  local ver
  ver="$("$ROOT/.venv/bin/python" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')"
  local major minor
  major="${ver%%.*}"
  minor="${ver#*.}"
  if (( major < 3 || (major == 3 && minor < 11) )); then
    log "В .venv нужен Python >= 3.11 (сейчас $ver). Удалите .venv и установите python3.11."
    exit 1
  fi
  if ! "$ROOT/.venv/bin/python" -c "import uvicorn" 2>/dev/null; then
    log "Ставлю зависимости сервисов в .venv…"
    "$ROOT/.venv/bin/pip" install -U pip -q
    local req
    for req in \
      account_service/requirements.txt \
      booking_service/requirements.txt \
      tracking_service/requirements.txt \
      media_service/requirements.txt \
      payment_service/requirements.txt \
      review_service/requirements.txt \
      notification_service/requirements.txt \
      gateway_service/requirements.txt; do
      require_file "$ROOT/$req"
      "$ROOT/.venv/bin/pip" install -r "$ROOT/$req" -q
    done
  fi
  if ! "$ROOT/.venv/bin/python" -c "import psycopg" 2>/dev/null; then
    log "Ставлю psycopg (нужен для alembic)…"
    "$ROOT/.venv/bin/pip" install 'psycopg[binary]' -q
  fi
}

check_env_files() {
  local svc
  for svc in account_service booking_service tracking_service media_service \
             payment_service review_service notification_service gateway_service; do
    if [[ ! -f "$ROOT/$svc/.env" ]]; then
      log "Нет $ROOT/$svc/.env — скопируйте env.sample: cp $svc/env.sample $svc/.env (и согласуйте SECRET_KEY / INTERNAL_API_TOKEN между сервисами)."
      exit 1
    fi
  done
}

wait_for_postgres() {
  local i
  for i in $(seq 1 60); do
    if docker compose -f "$ROOT/infra/docker-compose.yml" exec -T postgres \
        pg_isready -U dogapp >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  log "Postgres не поднялся за 60 с."
  return 1
}

migrate_service() {
  local name="$1"
  (cd "$ROOT/$name" && "$ROOT/.venv/bin/alembic" upgrade head)
}

migrate_booking() {
  # create_all в 0001_init совпадает с моделями; последующие ревизии частично дублируют схему.
  if (cd "$ROOT/booking_service" && "$ROOT/.venv/bin/alembic" upgrade head); then
    return 0
  fi
  log "booking_service: alembic upgrade head не прошёл — выполняю 0001_init + stamp head…"
  (cd "$ROOT/booking_service" && "$ROOT/.venv/bin/alembic" upgrade 0001_init)
  (cd "$ROOT/booking_service" && "$ROOT/.venv/bin/alembic" stamp head)
}

run_migrations() {
  migrate_service account_service
  migrate_booking
  migrate_service tracking_service
  migrate_service media_service
  migrate_service payment_service
  migrate_service review_service
  migrate_service notification_service
  log "Миграции применены."
}

port_in_use() {
  local port="$1"
  if command -v nc >/dev/null 2>&1; then
    nc -z 127.0.0.1 "$port" >/dev/null 2>&1
  else
    (echo >/dev/tcp/127.0.0.1/"$port") >/dev/null 2>&1
  fi
}

stop_previous() {
  if [[ -f "$ROOT/scripts/stop-all.sh" ]]; then
    bash "$ROOT/scripts/stop-all.sh" || true
  fi
  sleep 1
}

start_uvicorn() {
  local name="$1" subdir="$2" port="$3"
  if port_in_use "$port"; then
    log "Порт $port занят — пропускаю $name (остановите процесс или выполните scripts/stop-all.sh)."
    echo ""
    return 0
  fi
  mkdir -p "$LOG_DIR"
  pushd "$ROOT/$subdir" >/dev/null || exit 1
  nohup "$ROOT/.venv/bin/uvicorn" app.main:app \
    --host 0.0.0.0 --port "$port" --reload \
    >>"$LOG_DIR/${name}.log" 2>&1 &
  local pid=$!
  popd >/dev/null || true
  echo "$pid"
}

# --- main ---

cd "$ROOT"

if [[ "$FORCE" == true ]]; then
  stop_previous
fi

if port_in_use 8080 && [[ "$FORCE" != true ]] && [[ "$MIGRATE_ONLY" != true ]]; then
  log "Порт 8080 занят. Запустите с --force (остановит PID из .run/pids) или scripts/stop-all.sh."
  exit 1
fi

ensure_venv
check_env_files

mkdir -p "$RUN_DIR" "$LOG_DIR"
: >"$PID_FILE"

log "Запускаю Postgres (Docker)…"
docker compose -f "$ROOT/infra/docker-compose.yml" up -d
wait_for_postgres

mkdir -p "$ROOT/media_service/data/media_uploads"

if [[ "$DO_MIGRATE" == true ]]; then
  run_migrations
fi

if [[ "$MIGRATE_ONLY" == true ]]; then
  log "Режим --migrate-only: сервисы не запускаю."
  exit 0
fi

log "Запускаю uvicorn…"
for row in \
  "account:account_service:8000" \
  "booking:booking_service:8001" \
  "tracking:tracking_service:8002" \
  "media:media_service:8003" \
  "payment:payment_service:8004" \
  "review:review_service:8005" \
  "notification:notification_service:8006" \
  "gateway:gateway_service:8080"; do
  IFS=: read -r name dir port <<<"$row"
  pid="$(start_uvicorn "$name" "$dir" "$port")"
  if [[ -n "${pid// /}" ]]; then
    echo "$pid" >>"$PID_FILE"
  fi
done

sleep 2
if curl -sf "http://127.0.0.1:8080/health" >/dev/null; then
  log "Шлюз отвечает: http://127.0.0.1:8080/health"
else
  log "Шлюз пока не отвечает; смотрите логи в $LOG_DIR"
fi

log "Остановка: $ROOT/scripts/stop-all.sh"
log "Логи: $LOG_DIR"
