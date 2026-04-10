#!/bin/sh
set -e
if [ -f /app/alembic.ini ]; then
  alembic upgrade head
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
