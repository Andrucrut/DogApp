#!/usr/bin/env bash
# Создаёт двух демо-пользователей через account_service (POST /api/v1/auth/register).
# Монолит: задайте MONOLITH_BASE_URL или MONOLITH_URL (например https://….onrender.com).
# Микросервис: поднят account на порту 8000 или задайте ACCOUNT_URL.
#
# Учётные данные (после успешного запуска):
#   Владелец:  demo.owner@example.com  / DemoOwner1
#   Выгульщик: demo.walker@example.com / DemoWalker1
#
# Повторный запуск вернёт 409 Conflict, если пользователи уже есть.

set -euo pipefail
MONO="${MONOLITH_URL:-${MONOLITH_BASE_URL:-}}"
MONO="${MONO%/}"
if [[ -n "$MONO" && -z "${ACCOUNT_URL:-}" ]]; then
  ACCOUNT_URL="${MONO}/account"
elif [[ -z "${ACCOUNT_URL:-}" ]]; then
  ACCOUNT_URL="http://127.0.0.1:8000"
fi

register() {
  local body="$1"
  curl -sS -w "\nHTTP:%{http_code}\n" -X POST "${ACCOUNT_URL}/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "$body"
}

echo "=== Владелец (owner) ==="
register '{"email":"demo.owner@example.com","first_name":"Демо","last_name":"Владелец","consent_personal_data":true,"consent_privacy_policy":true,"password":"DemoOwner1","role_key":"owner"}'
echo
echo "=== Выгульщик (walker) ==="
register '{"email":"demo.walker@example.com","first_name":"Демо","last_name":"Выгульщик","consent_personal_data":true,"consent_privacy_policy":true,"password":"DemoWalker1","role_key":"walker"}'
echo
